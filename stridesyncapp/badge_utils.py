from .models import Badge, UserBadge

def check_and_award_badges(user, trigger_type, value, request=None):
    # Find eligible badges
    awarded = []
    badges = Badge.objects.filter(trigger_type=trigger_type, trigger_value__lte=value)
    for badge in badges:
        # Award only if user doesn't have it yet
        if not UserBadge.objects.filter(user=user, badge=badge).exists():
            UserBadge.objects.create(user=user, badge=badge)
            awarded.append(badge)
    if request is not None and awarded:
        request.session['awarded_badges'] = [b.id for b in awarded]  # Store only IDs!
    return awarded

