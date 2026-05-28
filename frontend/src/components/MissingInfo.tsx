export function MissingInfo({ items }: { items: string[] }) {
  if (!items.length) {
    return <div className="ok">关键字段暂无缺失提醒</div>;
  }
  return (
    <div className="warning">
      <strong>缺失信息：</strong>
      {items.join("、")}
    </div>
  );
}
