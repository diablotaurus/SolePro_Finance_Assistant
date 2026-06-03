"""
Middleware для проверки доступа пользователей.
"""
from typing import List, Optional

from telegram import Update
from telegram.ext import BaseHandler


class AccessMiddleware(BaseHandler):
    """
    Middleware для проверки доступа пользователей.
    
    Проверяет, есть ли пользователь в списке разрешенных пользователей.
    """
    
    def __init__(self, allowed_users: List[int]):
        """
        Инициализировать middleware.
        
        Args:
            allowed_users: Список ID разрешенных пользователей
        """
        super().__init__(callback=self._handle, block=True)
        self.allowed_users = allowed_users

    async def _handle(self, update: Update, context) -> None:
        """Handle unauthorized access with a user-facing message."""
        if update.effective_message:
            await update.effective_message.reply_text(
                "❌ Доступ запрещен!\n\n"
                "У вас нет прав для использования этого бота.\n"
                "Обратитесь к администратору."
            )

    def check_update(self, update: Update) -> Optional[bool]:
        """
        Проверить обновление.
        
        Args:
            update: Обновление для проверки
            
        Returns:
            True если обновление разрешено, False если запрещено, None если пропустить
        """
        # Проверяем, есть ли пользователь в обновлении
        user = None
        
        if update.effective_user:
            user = update.effective_user
        elif update.message and update.message.from_user:
            user = update.message.from_user
        elif update.callback_query and update.callback_query.from_user:
            user = update.callback_query.from_user
        elif update.inline_query and update.inline_query.from_user:
            user = update.inline_query.from_user
        
        if not user:
            # Если нет пользователя, пропускаем
            return None
        
        # Если список пустой, разрешаем всем (удобно для разработки)
        if not self.allowed_users:
            return False

        # True => этот handler обработает апдейт и заблокирует остальные
        return user.id not in self.allowed_users
