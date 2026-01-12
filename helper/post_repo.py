from sqlalchemy import text
from typing import List, Dict
from helper.database import AsyncSessionLocal

class PostsRepository:
    def __init__(self):
        pass

    async def get_existing_external_ids(
        self,
        platform: str,
        external_ids: List[str],
    ) -> set:
        if not external_ids:
            return set()

        query = text("""
            SELECT external_id
            FROM posts
            WHERE platform = :platform
              AND external_id = ANY(:external_ids)
        """)

        async with AsyncSessionLocal() as session:
            result = await session.execute(
                query,
                {
                    "platform": platform,
                    "external_ids": external_ids,
                }
            )

            return {row[0] for row in result.fetchall()}

    async def insert_posts(self, posts: List[Dict]):
        if not posts:
            return

        query = text("""
            INSERT INTO posts (
                platform,
                external_id,
                url,
                title,
                content,
                author,
                published_at,
                score,
                engagement
            )
            VALUES (
                :platform,
                :external_id,
                :url,
                :title,
                :content_text,
                :author,
                :published_at,
                :intent_score,
                :engagement
            )
            ON CONFLICT (platform, external_id)
            DO NOTHING
        """)

        async with AsyncSessionLocal() as session:
            await session.execute(query, posts)
            await session.commit()