import { FilePlus, PlayCircle, Trash2 } from "lucide-react";
import { CaseListItem, api } from "../api";

type Props = {
  cases: CaseListItem[];
  onRefresh: () => void;
  onNew: () => void;
  onOpen: (id: number, page?: string) => void;
};

export function CaseListPage({ cases, onRefresh, onNew, onOpen }: Props) {
  async function seedDemo() {
    const created = await api.seedDemo();
    onRefresh();
    onOpen(created.id, "recommendation");
  }

  async function remove(id: number) {
    if (!window.confirm("确认删除该病例？")) return;
    await api.deleteCase(id);
    onRefresh();
  }

  return (
    <main className="content">
      <div className="page-header">
        <div>
          <h1>病例列表</h1>
          <p>本地个人病例整理与规则匹配</p>
        </div>
        <div className="actions">
          <button onClick={seedDemo} title="加入示例病例">
            <PlayCircle size={18} /> 示例
          </button>
          <button className="primary" onClick={onNew}>
            <FilePlus size={18} /> 新建病例
          </button>
        </div>
      </div>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>姓名/编号</th>
              <th>年龄</th>
              <th>侧别</th>
              <th>大小</th>
              <th>cN</th>
              <th>M</th>
              <th>更新</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            {cases.map((item) => (
              <tr key={item.id}>
                <td>{item.patient_name_or_code}</td>
                <td>{item.age ?? "-"}</td>
                <td>{item.laterality ?? "-"}</td>
                <td>{item.tumor_size_cm ? `${item.tumor_size_cm} cm` : "-"}</td>
                <td>{item.clinical_node_status ?? "-"}</td>
                <td>{item.distant_metastasis ?? "-"}</td>
                <td>{item.updated_at.replace("T", " ")}</td>
                <td className="row-actions">
                  <button onClick={() => onOpen(item.id, "edit")}>编辑</button>
                  <button onClick={() => onOpen(item.id, "recommendation")}>推荐</button>
                  <button className="icon danger" onClick={() => remove(item.id)} title="删除">
                    <Trash2 size={16} />
                  </button>
                </td>
              </tr>
            ))}
            {!cases.length && (
              <tr>
                <td colSpan={8} className="empty">暂无病例</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </main>
  );
}
