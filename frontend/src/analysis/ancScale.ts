export const ANC_BREAK_COLORS = ['#dbe9f6', '#a9c6e3', '#78a3d0', '#4780bd', '#1a5276'];

export const ANC_BIN_COUNT = 5;

export interface AncBreaks {
  edges: number[];
  min: number;
  max: number;
}

export function computeAncBreaks(values: Array<number | null | undefined>): AncBreaks {
  const sorted = values
    .filter((v): v is number => typeof v === 'number' && Number.isFinite(v))
    .sort((a, b) => a - b);
  if (sorted.length === 0) {
    return { edges: [], min: 0, max: 0 };
  }
  const edges: number[] = [];
  for (let i = 1; i < ANC_BIN_COUNT; i++) {
    const idx = Math.floor((i / ANC_BIN_COUNT) * sorted.length);
    edges.push(sorted[Math.min(idx, sorted.length - 1)]);
  }
  return { edges, min: sorted[0], max: sorted[sorted.length - 1] };
}

export function ancColor(value: number | null | undefined, breaks: AncBreaks): string | null {
  if (value == null || !Number.isFinite(value) || breaks.edges.length === 0) return null;
  let bin = breaks.edges.findIndex((edge) => value < edge);
  if (bin === -1) bin = breaks.edges.length;
  return ANC_BREAK_COLORS[Math.min(bin, ANC_BREAK_COLORS.length - 1)];
}

export function ancLegendLabels(breaks: AncBreaks): string[] {
  if (breaks.edges.length === 0) return [];
  const fmt = (v: number) => (v >= 100 ? v.toFixed(0) : v.toFixed(0));
  const low = `≤${fmt(breaks.edges[0])}%`;
  const middle = breaks.edges.slice(0, -1).map((e, i) => `${fmt(e)}–${fmt(breaks.edges[i + 1])}%`);
  const high = `${fmt(breaks.edges[breaks.edges.length - 1])}+% (up to ${fmt(breaks.max)}%)`;
  return [low, ...middle, high];
}