#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
语音认证模块
包含声纹识别、主动交流和AI日记功能
"""

from .voiceprint_auth import VoiceprintAuthenticator, get_voiceprint_auth
from .active_communication import ActiveCommunicationManager, get_active_comm_manager
from .ai_diary import AIDiaryManager, get_ai_diary_manager

__all__ = [
    'VoiceprintAuthenticator',
    'get_voiceprint_auth',
    'ActiveCommunicationManager',
    'get_active_comm_manager',
    'AIDiaryManager',
    'get_ai_diary_manager'
]
