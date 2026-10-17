from fastapi.testclient import TestClient
from main import app

def test_non_ai_endpoints_and_acceptance_values():
    with TestClient(app) as c:
        health=c.get('/api/health').json()
        assert health['counts']=={'patients':13400,'hcps':6000,'reps':200}
        o=c.get('/api/overview').json()
        assert o['monthly_revenue_usd']==133740000.0
        assert o['high_risk_patients']==1883
        assert abs(c.get('/api/waterfall?scenario=Base').json()['steps'][-1]['revenue_usd']-714880000)<1000
        assert len(c.get('/api/hcps').json()['call_gaps'])==154
        assert len(c.get('/api/roi').json()['interventions'])==4
        assert c.get('/api/patients').status_code==200
        assert c.get('/api/reps').status_code==200
        assert c.post('/api/what-if',json={'carepath_effect':.4,'switch_per_overdue_day':.03,'risk_cutoff':.3}).status_code==200
        names=c.get('/api/quick-questions').json()['questions']
        assert len(names)>=18
        for name in names:
            assert c.get('/api/quick-questions/'+name.replace(' ','%20')).status_code==200
        assert c.get('/api/assumptions').status_code==200
        assert c.get('/api/reconciliation').status_code==200

def test_ai_features_fail_gracefully_without_key(monkeypatch):
    monkeypatch.delenv('GEMINI_API_KEY', raising=False)
    monkeypatch.delenv('GOOGLE_API_KEY', raising=False)
    with TestClient(app) as c:
        briefing=c.post('/api/insights/briefing',json={'page':'Overview','query_results':{'monthly_revenue_usd':133740000}})
        assert briefing.status_code==200
        assert briefing.json()['available'] is False
        assert 'rule-based' in briefing.json()['message'].lower()
        chat=c.post('/api/chat',json={'question':'How many high-risk patients are there?','history':[]})
        assert chat.status_code==200
        assert chat.json()['available'] is False

def test_sql_guard_allows_select_and_rejects_writes():
    from main import _validate_and_run_sql
    assert _validate_and_run_sql('SELECT COUNT(*) AS n FROM patients')[0]['n']==13400
    try:
        _validate_and_run_sql('DELETE FROM patients')
        assert False, 'Write query should be rejected'
    except ValueError:
        pass


def test_patient_and_hcp_filters_update_aggregates_and_true_counts():
    with TestClient(app) as c:
        all_patients=c.get('/api/patients').json()
        assert all_patients['total_matching']==13400
        assert all_patients['returned_rows']==500
        assert sum(r['count'] for r in all_patients['risk_distribution'])==13400
        high=c.get('/api/patients?risk=High').json()
        assert high['total_matching']==1883
        assert sum(r['count'] for r in high['risk_distribution'])==1883
        assert all(r['risk_level']=='High' for r in high['rows'])
        all_hcps=c.get('/api/hcps').json()
        assert all_hcps['total_matching']==6000
        tier1=c.get('/api/hcps?tier=Tier%201').json()
        assert tier1['total_matching'] < all_hcps['total_matching']
        assert all(r['tier']=='Tier 1' for r in tier1['rows'])
        assert all(r['tier']=='Tier 1' for r in tier1['tier_distribution'])

def test_roi_sensitivity_scales_each_intervention_baseline():
    with TestClient(app) as c:
        baseline=c.get('/api/roi').json()['interventions']
        unchanged=c.get('/api/roi?effectiveness_scale=1&uptake_scale=1&realisation_scale=1').json()['interventions']
        assert [round(x['roi_multiple'], 6) for x in baseline] == [round(x['roi_multiple'], 6) for x in unchanged]
        scaled=c.get('/api/roi?effectiveness_scale=0.5&uptake_scale=1&realisation_scale=1').json()['interventions']
        assert all(abs(x['effectiveness'] - y['effectiveness']*0.5) < 1e-9 for x,y in zip(scaled,baseline))

def test_sql_guard_allows_safe_cte_and_still_blocks_unsafe_sql():
    from main import _validate_and_run_sql, _grounded_text
    result=_validate_and_run_sql('WITH patient_count AS (SELECT COUNT(*) AS n FROM patients) SELECT n FROM patient_count')
    assert result[0]['n']==13400
    assert _grounded_text('Current revenue is $133.74M.', {'monthly_revenue_usd':133740000})
    for sql in [
        'WITH x AS (SELECT * FROM sqlite_master) SELECT * FROM x',
        'WITH x AS (SELECT COUNT(*) AS n FROM patients) DELETE FROM patients',
        'WITH x AS (SELECT COUNT(*) AS n FROM patients); SELECT * FROM x',
        'SELECT load_extension(1) FROM patients',
    ]:
        try:
            _validate_and_run_sql(sql)
            assert False, f'Unsafe query should be rejected: {sql}'
        except ValueError:
            pass
