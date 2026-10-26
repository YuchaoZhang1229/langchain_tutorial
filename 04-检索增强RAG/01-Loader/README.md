## 文档加载

### 为什么要文档加载
- **统一数据结构**：不同格式的文档（PDF、Word、网页等）转成统一的 `Document` 对象，通常包含 `page_content`（文本内容） 和 `metadata`（元数据）
- **元数据设计**：提取来源、页码、章节、更新时间等元数据，后续可用于**元数据索引过滤**、**权限控制**和**答案引用**

### 文档加载方法
| 格式 | 加载器 | 依赖 | 
|------|--------|------|
| `.txt` | `TextLoader` | 无 | 
| `.pdf` | `PyPDFLoader` | `pypdf` |
| `.docx` | `Docx2txtLoader` | `docx2txt` | 
| `.md` | `UnstructuredMarkdownLoader` | `unstructured` |
| `.csv` | `CSVLoader` | 无 | 
| `.json` | `JSONLoader` | `jq` | 
| 网页 | `WebBaseLoader` | `bs4` | 
| 批量目录 | `DirectoryLoader` | 视子类型 |


### 文档加载的最佳实践
#### 1. 清洗与预处理
- 保留标题层级结构（H1, H2, H3...）→ 后续分块的关键依据 
- 表格转为 Markdown 格式 → 方便后续向量化 
- 图片生成文字描述（caption）→ 让图片内容也可被检索 
- 去除页眉、页脚、页码、水印等噪声

#### 2. 加载方式
- `load()` 是一次性全读进内存，大文件建议用 `lazy_load()` 迭代式加载，避免 
- 网络类加载器（如网页、API）有异步版本 `aload()` / `alazy_load()`，批量抓取时能省不少时间

#### 3. 元数据设计
- 保留元数据：source、page、date等 -> 便于溯源、过滤和权限控制


