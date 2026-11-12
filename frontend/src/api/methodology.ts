export interface MethodologyItem {
  category: string;
  title: string;
  value: string;
}

export async function getMethodology(): Promise<{items: MethodologyItem[]}> {
  const { apiGet } = await import('./client');
  return apiGet<{items: MethodologyItem[]}>('/api/methodology');
}
