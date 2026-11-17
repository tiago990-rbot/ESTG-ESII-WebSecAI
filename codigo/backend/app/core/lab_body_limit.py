"""Bound new input endpoints before JSON parsing, including chunked requests."""
from starlette.responses import JSONResponse

class LabBodyLimit:
    def __init__(self,app):self.app=app
    async def __call__(self,scope,receive,send):
        path=scope.get('path','')
        if scope['type']=='http' and path.startswith(('/api/v1/lab','/api/v1/usage')):
            original_send=send
            async def private_send(message):
                if message['type']=='http.response.start':
                    message={**message,'headers':[(k,v) for k,v in message.get('headers',[]) if k.lower()!=b'cache-control']+[(b'cache-control',b'no-store')]}
                await original_send(message)
            send=private_send
        if scope['type']!='http' or not path.startswith(('/api/v1/lab','/api/v1/usage')) or scope.get('method') not in {'POST','PUT','PATCH'}:
            return await self.app(scope,receive,send)
        maximum=16000 if path.startswith('/api/v1/usage') else 2_000_000
        body=bytearray()
        while True:
            message=await receive()
            if message['type']=='http.disconnect':return
            body.extend(message.get('body',b''))
            if len(body)>maximum:
                return await JSONResponse({'detail':'Pedido acima do limite de tamanho.'},status_code=413)(scope,receive,send)
            if not message.get('more_body',False):break
        sent=False
        async def bounded_receive():
            nonlocal sent
            if sent:return await receive()
            sent=True;return {'type':'http.request','body':bytes(body),'more_body':False}
        await self.app(scope,bounded_receive,send)
