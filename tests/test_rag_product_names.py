"""Assistant answers use the product names the dashboard shows, never internal keys."""
import pytest

from backend.rag import inspection_facts


@pytest.mark.parametrize('category,shown', [('pcb1', 'PCB 1'), ('macaroni2', 'Macaroni 2'),
                                            ('pipe_fryum', 'pipe fryum'), ('chewinggum', 'chewing gum'),
                                            ('new_item', 'new item'), (None, 'selected product')])
def test_answer_names_the_product_like_the_dashboard(category, shown):
    facts = inspection_facts('why is this result anomalous?', {'category': category, 'verdict': 'Anomalous',
                             'score': 0.6, 'threshold': 0.5, 'uncertainty_margin': 0.01})
    assert f'flagged this {shown} image' in facts['text']
