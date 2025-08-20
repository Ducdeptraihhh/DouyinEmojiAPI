import asyncio
import json
import logging
from urllib.parse import parse_qs, urlparse
from aiohttp import web
from emoticon_api import EmoticonAPI

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

api = EmoticonAPI()

async def handle_emoticon_api(request):
    """处理表情包API请求"""
    try:
        query = request.query
        ac = query.get('ac', '')
        wxid = query.get('wxid', '')
        start = int(query.get('start', 0))
        limit = int(query.get('limit', 40))
        keyword = query.get('keyword', '')
        from urllib.parse import unquote
        if keyword:
            keyword = unquote(keyword)
        logger.info(f"收到请求: ac={ac}, wxid={wxid}, start={start}, limit={limit}, keyword={keyword}")
        result = await api.process_request(ac, wxid, start, limit, keyword)
        return web.json_response(result)
        
    except Exception as e:
        logger.error(f"处理请求失败: {e}")
        error_response = {
            'msg': f'服务器错误: {str(e)}',
            'code': 500
        }
        return web.json_response(error_response, status=500)

async def handle_health_check(request):
    """健康检查接口"""
    return web.json_response({
        'status': 'ok',
        'message': '表情包API服务运行正常',
        'timestamp': asyncio.get_event_loop().time()
    })

async def init_app():
    """初始化应用"""
    app = web.Application()
    app.router.add_get('/emoticon_api.py', handle_emoticon_api)
    app.router.add_get('/emoticon_api', handle_emoticon_api)
    app.router.add_get('/api/emoticon', handle_emoticon_api)
    app.router.add_get('/health', handle_health_check)
    app.router.add_static('/downloads', path='downloads', name='downloads')
    return app

def main():
    """主函数"""
    logger.info("启动表情包API服务器...")
    app = init_app()
    web.run_app(
        app,
        host='0.0.0.0',
        port=8000,
        access_log=logger
    )

if __name__ == '__main__':
    main()
