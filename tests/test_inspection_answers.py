from backend.rag import EvidenceWorkflow
from backend.config import Settings


def record(verdict='Anomalous',score=.09091377):
    return {'id':'a'*32,'category':'pcb1','verdict':verdict,'score':score,'threshold':.0478025,
            'uncertainty_margin':.0023901,'model_id':'real-measurement-fixture'}


def test_verdict_question_answers_the_inspected_record_without_llm_or_retrieval():
    answer=EvidenceWorkflow(Settings(),None).run('so this product is anomaly right?',record())
    assert answer['mode']=='measurement_only'
    assert answer['answer'].startswith('Yes—')
    assert '0.09091' in answer['answer'] and '0.04780' in answer['answer']
    assert answer['measurement_summary']['source']=='saved_inspection'
    assert answer['evidence']==[]


def test_same_question_uses_current_record_not_previous_anomalous_answer():
    answer=EvidenceWorkflow(Settings(),None).run('is this anomalous?',record('Good',.02),
        [{'role':'assistant','text':'Yes, anomalous'}])
    assert answer['answer'].startswith('No—') and 'Good' in answer['answer']
    assert '0.02000' in answer['answer']


def test_score_question_does_not_present_it_as_accuracy():
    for question in ('does the score mean accuracy?', 'Does 0.09 mean 9% accurate?'):
        answer=EvidenceWorkflow(Settings(),None).run(question,record())
        assert answer['mode']=='measurement_only'
        assert '0.09091' in answer['answer']
        assert 'not an accuracy percentage' in answer['answer']
        assert 'defect probability' in answer['answer']


def test_uncertainty_reports_band_instead_of_asserting_anomaly():
    answer=EvidenceWorkflow(Settings(),None).run('is it anomalous?',record('Uncertain',.048))
    assert answer['answer'].startswith('No—') and 'within the review band' in answer['answer']


def test_unsupported_root_cause_still_abstains_but_keeps_measured_result():
    answer=EvidenceWorkflow(Settings(),None).run('What caused this defect?',record())
    assert answer['mode']=='abstained'
    assert '0.09091' in answer['answer'] and 'do not establish' in answer['answer']


def test_yes_no_cause_question_cannot_bypass_scope_checks():
    answer=EvidenceWorkflow(Settings(),None).run('Is this defect caused by heat?',record())
    assert answer['mode']=='abstained' and not answer['answer'].startswith('Yes')


def test_negated_question_reports_the_saved_verdict_without_an_ambiguous_yes():
    answer=EvidenceWorkflow(Settings(),None).run('Is this not anomalous?',record())
    assert answer['mode']=='measurement_only'
    assert answer['answer'].startswith('The model flagged') and 'Anomalous' in answer['answer']
