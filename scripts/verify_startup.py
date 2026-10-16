import json
import platform
import importlib.metadata
from PIL import Image
from fastapi.testclient import TestClient
from backend.main import app

if __name__=='__main__':
    with TestClient(app) as client:
        assert client.get('/api/health').status_code==200
        assert client.get('/').status_code==200
        sample=next((app.state.detector.settings.root/'samples').glob('*.jpg'))
        result,_=app.state.detector.predict(Image.open(sample),sample.stem.split('_')[0])
        assert result['score']>=0
        report={'startup':'passed','python':platform.python_version(),'torch':importlib.metadata.version('torch'),
                'transformers':importlib.metadata.version('transformers'),'real_model_prediction':result}
        (app.state.detector.settings.root/'results'/'startup_verification.json').write_text(json.dumps(report,indent=2))
        print(json.dumps(report,indent=2))
