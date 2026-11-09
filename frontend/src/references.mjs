// Closest normal reference photos shown under an inspection result. Pure helpers so they can be tested.
export const referenceUrl = category => `./assets/references/${category}.json`;

// Photos of one product look alike, so a percentage would sit near 99% for all of them; the order is what matters.
export const rankLabel = index => ['Closest match', '2nd closest', '3rd closest'][index] || `${index + 1}th closest`;

// The record names the closest photos (id + similarity); the library file supplies their thumbnails.
export function pickReferences(record, library) {
  const byId = new Map((library?.items || []).map(item => [item.id, item]));
  return (record?.references || [])
    .map(reference => ({id: reference.id, similarity: reference.similarity, thumb: byId.get(reference.id)?.thumb}))
    .filter(reference => reference.thumb);
}
