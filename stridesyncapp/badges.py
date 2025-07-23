from django.db.models import Sum
from .models import Badge, UserBadge

def trigger_badges_for_user(user):
    """
    Check and award any new badges a user qualifies for.
    Should be called immediately after streak or step recalculation.
    
    Args:
        user (User): The user instance to check badges for.
    
    Returns:
        List of Badge instances that were newly awarded.
    
    Usage:
        # After recalculating streaks/steps for a user:
        # from .badges import trigger_badges_for_user
        # trigger_badges_for_user(user)
    """
    awarded_badge_ids = set(user.badges.values_list('badge_id', flat=True))
    new_badges = []

    # 1. Streak-based badges
    user_streak = getattr(user, 'streak', None)
    if user_streak:
        streak = user_streak.current_streak
        streak_badges = Badge.objects.filter(trigger_type='streak', trigger_value__lte=streak)
        for badge in streak_badges:
            if badge.id not in awarded_badge_ids:
                UserBadge.objects.create(user=user, badge=badge)
                new_badges.append(badge)

    # 2. Steps-based badges (total steps)
    total_steps = user.steps.aggregate(total=Sum('step_count'))['total'] or 0
    step_badges = Badge.objects.filter(trigger_type='steps', trigger_value__lte=total_steps)
    for badge in step_badges:
        if badge.id not in awarded_badge_ids:
            UserBadge.objects.create(user=user, badge=badge)
            new_badges.append(badge)

    # 3. Leaderboard badges
    # leaderboard_badges = Badge.objects.filter(trigger_type='leaderboard' ...)

    return new_badges


# To use this, import and call after streak/step update:
# from .badges import trigger_badges_for_user
# trigger_badges_for_user(user)
