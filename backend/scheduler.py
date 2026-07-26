import asyncio
import logging
from datetime import datetime
from typing import Dict, Any
from backend.pipeline import Phase1Pipeline
from backend.phase2_pipeline import Phase2Pipeline
from backend.phase3_pipeline import Phase3Pipeline

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] [%(levelname)s] %(message)s")


class ContinuousPipelineScheduler:
    """
    Automated Continuous Ingestion & Vector Index Maintenance Scheduler.
    Runs periodic background tasks to update customer feedback reviews, 
    re-index vector store embeddings, and refresh export files.
    """

    def __init__(self, interval_hours: float = 24.0):
        self.interval_seconds = interval_hours * 3600.0
        self.is_running = False
        self.last_run_timestamp = None

    async def execute_full_pipeline_cycle(self) -> Dict[str, Any]:
        """Executes a complete end-to-end pipeline update cycle."""
        logging.info("Starting scheduled continuous pipeline update cycle...")
        self.last_run_timestamp = datetime.now().isoformat()

        # 1. Run Phase 1 Ingestion, PII Normalization & Exports (Synchronous)
        p1 = Phase1Pipeline()
        summary_obj, sanitized_entries, chunks = p1.run_pipeline()
        res1 = summary_obj.model_dump()
        logging.info(f"Phase 1 Ingestion Completed: {res1.get('total_sanitized_valid')} valid reviews.")

        # 2. Run Phase 2 ABSA & Vector Embedding Indexing (Asynchronous)
        p2 = Phase2Pipeline()
        res2 = await p2.run_pipeline()
        logging.info(f"Phase 2 Vector Embedding Completed: {res2.get('total_chunks_embedded')} chunks embedded.")

        # 3. Run Phase 3 Grounded RAG Assistant Verification (Asynchronous)
        p3 = Phase3Pipeline()
        res3 = await p3.run_pipeline()
        logging.info("Phase 3 Verification Completed.")

        summary = {
            "timestamp": self.last_run_timestamp,
            "status": "SUCCESS",
            "phase1_summary": res1,
            "phase2_summary": res2,
            "phase3_summary": res3,
        }

        logging.info("Scheduled continuous pipeline update cycle completed successfully.")
        return summary

    async def start_scheduler_loop(self):
        """Starts the background continuous scheduler loop."""
        self.is_running = True
        logging.info(f"Scheduler loop initialized. Running every {self.interval_seconds / 3600.0} hours.")
        
        while self.is_running:
            try:
                await self.execute_full_pipeline_cycle()
            except Exception as e:
                logging.error(f"Scheduler pipeline cycle error: {str(e)}")
            
            # Sleep until next scheduled cycle
            await asyncio.sleep(self.interval_seconds)

    def stop_scheduler(self):
        """Stops the continuous scheduler loop."""
        self.is_running = False
        logging.info("Scheduler loop stopped.")


if __name__ == "__main__":
    scheduler = ContinuousPipelineScheduler(interval_hours=24.0)
    asyncio.run(scheduler.execute_full_pipeline_cycle())
