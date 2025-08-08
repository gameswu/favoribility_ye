from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from astrbot.api import logger, AstrBotConfig

import os
import json

@register("favoribility_ye", "gameswu", "这是一个为小夜提供好感度评估的插件", "0.1.1", "https://github.com/gameswu/favoribility_ye")
class MyPlugin(Star):
    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        self.config = config
        self.max_value = config.get("max_value")
        self.min_value = config.get("min_value")
        self.init_value = config.get("init_value")
        self.max_change = config.get("max_change")

    async def initialize(self):
        """可选择实现异步的插件初始化方法，当实例化该插件类之后会自动调用该方法。"""
        # 检查数据存储文件夹是否存在并创建，路径为二级父目录下的 favoribility_ye文件夹
        self.data_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "favoribility_ye")
        if not os.path.exists(self.data_path):
            os.makedirs(self.data_path)

        # 检查数据文件是否存在并创建，路径为 favoribility_ye文件夹下的 data.json
        self.data_file = os.path.join(self.data_path, "data.json")
        if not os.path.exists(self.data_file):
            with open(self.data_file, "w") as f:
                json.dump({}, f)

    async def _get_favoribility(self, user_id):
        """获取用户的好感度"""
        with open(self.data_file, "r") as f:
            data = json.load(f)
        return data.get(str(user_id), self.init_value)

    async def _set_favoribility(self, user_id, value):
        """设置用户的好感度"""
        with open(self.data_file, "r") as f:
            data = json.load(f)
        data[str(user_id)] = value
        with open(self.data_file, "w") as f:
            json.dump(data, f)

    @filter.command("查看好感")
    async def check_favoribility(self, event: AstrMessageEvent, user_id: str = None):
        """查看好感度"""
        if user_id is None:
            user_id = event.get_sender_id()
        favoribility = await self._get_favoribility(user_id)
        yield event.plain_result(f"用户{user_id}的好感度为：{favoribility}/{self.max_value}")

    @filter.permission_type(filter.PermissionType.ADMIN)
    @filter.command("设置好感")
    async def set_favoribility(self, event: AstrMessageEvent, user_id: str, value: int):
        """设置用户的好感度"""
        await self._set_favoribility(user_id, value)
        yield event.plain_result(f"用户{user_id}的好感度已设置为：{value}/{self.max_value}")

    @filter.llm_tool("change_favoribility")
    async def change_favoribility(self, event: AstrMessageEvent, value: int):
        """改变对用户的好感度
        
        Args:
            value(number): 改变的值，正数增加好感度，负数减少好感度
        """
        user_id = event.get_sender_id()
        value = min(max(value, -self.max_change), self.max_change)
        favoribility = await self._get_favoribility(user_id)
        new_value = min(max(favoribility + value, self.min_value), self.max_value)
        await self._set_favoribility(user_id, new_value)
        return f"你对用户{user_id}的好感度增加了{value}，当前好感度为：{new_value}/{self.max_value}"
    
    @filter.llm_tool("get_favoribility")
    async def get_favoribility(self, event: AstrMessageEvent):
        """获取对用户的好感度"""
        user_id = event.get_sender_id()
        favoribility = await self._get_favoribility(user_id)
        return f"你对用户{user_id}的好感度为：{favoribility}/{self.max_value}"

    async def terminate(self):
        """可选择实现异步的插件销毁方法，当插件被卸载/停用时会调用。"""
