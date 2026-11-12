interface DatasetOverviewProps {
  totalRecords: number;
  stateDistrictUnits: number;
  stateCount: number;
  coverageStart: number;
  coverageEnd: number;
}

export default function DatasetOverview({
  totalRecords,
  stateDistrictUnits,
  stateCount,
  coverageStart,
  coverageEnd,
}: DatasetOverviewProps) {
  const items = [
    { label: 'District-Year Records', value: totalRecords.toLocaleString() },
    { label: 'District\u2013State Units', value: stateDistrictUnits.toLocaleString() },
    { label: 'States', value: stateCount.toLocaleString() },
    { label: 'Coverage', value: `${coverageStart}\u2013${coverageEnd}` },
  ];

  return (
    <section className="section">
      <h2 className="section-title">Dataset Overview</h2>
      <dl className="dataset-list">
        {items.map((item) => (
          <div className="dataset-item" key={item.label}>
            <dt className="dataset-label">{item.label}</dt>
            <dd className="dataset-value">{item.value}</dd>
          </div>
        ))}
      </dl>
    </section>
  );
}
