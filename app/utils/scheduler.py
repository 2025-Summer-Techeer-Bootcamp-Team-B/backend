import asyncio
from apscheduler.schedulers.background import BackgroundScheduler
from app.services.crawling_service.async_crawler import scrape_all_articles_async


def start_scheduler(app):
    scheduler = BackgroundScheduler()

    def run_crawling():
        # 비동기 함수는 이벤트 루프에서 실행
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(scrape_all_articles_async(max_concurrent=10, save_to_db=True))
        loop.close()

    # 15분마다 실행
    scheduler.add_job(run_crawling, 'interval', minutes=15)
    scheduler.start()
    app.state.scheduler = scheduler