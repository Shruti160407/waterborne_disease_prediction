import sys
sys.path.insert(0, 'd:\\waterborne_disease_prediction_model')
from backend.app import create_app

app = create_app()
client = app.test_client()

res = client.post('/api/auth/signup', json={'name':'t','email':'t@t.com','password':'t'})
print("RESPONSE STATUS:", res.status_code)
print("RESPONSE DATA:", res.get_data(as_text=True))
