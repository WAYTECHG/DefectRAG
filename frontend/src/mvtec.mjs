// Rows and cards for the MVTec AD section of the Official benchmark page. Pure functions so they can be tested.
const mark = interval => (!interval ? '' : interval[0] > 0 ? 'better' : interval[1] < 0 ? 'worse' : '');

export const productLabel = key => {
  const text = String(key).replace(/_/g, ' ');
  return text.charAt(0).toUpperCase() + text.slice(1);
};

export function mvtecCards(summary) {
  return (summary?.arms || []).map(arm => ({
    key: arm.key,
    label: arm.label,
    auroc: summary.macro_mean?.[arm.key]?.auroc,
    pixel: summary.macro_mean?.[arm.key]?.pixel_auroc,
  }));
}

export function mvtecRows(summary) {
  const arms = (summary?.arms || []).map(arm => arm.key);
  return Object.entries(summary?.categories || {}).map(([key, product]) => ({
    key,
    label: productLabel(key),
    tests: product.n_test,
    values: arms.map(arm => product.arms?.[arm]?.auroc),
    pixel: product.arms?.[arms[arms.length - 1]]?.pixel_auroc,
    // Clear differences from the paired bootstrap: coreset vs random memory, fine-tune vs coreset.
    coreset: mark(product.differences?.['B-A']),
    tuned: mark(product.differences?.['C-B']),
  }));
}

export const markSymbol = value => (value === 'better' ? '▲' : value === 'worse' ? '▼' : '');
