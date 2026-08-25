from langgraph.constants import END
from langgraph.graph import StateGraph

from atguigu.import_process.nodes.node_bge_embedding import NodeBGEEmbedding
from atguigu.import_process.nodes.node_document_split import NodeDocumentSplit
from atguigu.import_process.nodes.node_entry import NodeEntry
from atguigu.import_process.nodes.node_import_milvus import NodeImportMilvus
from atguigu.import_process.nodes.node_item_name_recognition import NodeItemNameRecognition
from atguigu.import_process.nodes.node_md_img import NodeMDImg
from atguigu.import_process.nodes.node_pdf_to_md import NodePDFToMD
from atguigu.import_process.state import ImportGraphState


class MainGraph:
    def __init__(self):
        self.build = StateGraph(ImportGraphState)
        self.add_notes()
        self.add_edges()
        self.graph = None

    def add_notes(self):
        self.build.add_node(NodeEntry.name,NodeEntry())
        self.build.add_node(NodePDFToMD.name,NodePDFToMD())
        self.build.add_node(NodeMDImg.name,NodeMDImg())
        self.build.add_node(NodeDocumentSplit.name,NodeDocumentSplit())
        self.build.add_node(NodeItemNameRecognition.name,NodeItemNameRecognition())
        self.build.add_node(NodeBGEEmbedding.name,NodeBGEEmbedding())
        self.build.add_node(NodeImportMilvus.name,NodeImportMilvus())
    def add_edges(self):
        self.build.set_entry_point(NodeEntry.name)
        self.build.add_conditional_edges(NodeEntry.name,self.router)
        self.build.add_edge(NodePDFToMD.name,NodeMDImg.name)
        self.build.add_edge(NodeMDImg.name,NodeDocumentSplit.name)
        self.build.add_edge(NodeDocumentSplit.name,NodeItemNameRecognition.name)
        self.build.add_edge(NodeItemNameRecognition.name,NodeBGEEmbedding.name)
        self.build.add_edge(NodeBGEEmbedding.name,NodeImportMilvus.name)

    def router(self,state:ImportGraphState):
        is_md_read_enabled=state.get("is_md_read_enabled",False)
        is_pdf_read_enabled=state.get("is_pdf_read_enabled",False)
        if is_md_read_enabled:
            return NodeMDImg.name
        elif is_pdf_read_enabled:
            return NodePDFToMD.name
        else:
            END

    def graph_run(self, state: ImportGraphState):
        if self.graph is None:
            self.graph = self.build.compile()
        self.graph=self.graph.invoke(state)
        return self.graph
    @classmethod
    def start_and_run(cls, state: ImportGraphState):
        return cls().graph_run(state)

if __name__ == '__main__':
    init_state_path={
        "local_file_path":r"D:\pojie\渊哥\hak180产品安全手册.pdf",
        "local_dir": r"D:\pojie\渊哥"
    }
    res=MainGraph.start_and_run(init_state_path)
    print(res)
