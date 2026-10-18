from backend.config import Settings
from backend.rag import KnowledgeIndex

if __name__=='__main__':
    settings=Settings()
    index=KnowledgeIndex(settings.root,settings.root/'knowledge'/'index')
    index.ensure()
    print('Indexed',len(index.documents),'source-attributed passages')
