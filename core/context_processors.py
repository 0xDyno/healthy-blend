from django.contrib import messages


def message_processor(request):
    message_data = []
    for message in messages.get_messages(request):
        message_data.append({
            'level': message.level_tag,
            'message': str(message),
            'extra_tags': message.extra_tags
        })
    return {'django_messages': message_data}
