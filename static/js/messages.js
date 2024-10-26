// static/js/messages.js

// Настройки для toastr
toastr.options = {
    "closeButton": true,
    "progressBar": true,
    "timeOut": "5000",
    "positionClass": "toast-top-right"
};

// Объект для управления сообщениями
const MessageManager = {
    // Показать обычное уведомление
    showToast: function (message, type = 'info') {
        toastr[type](message);
    },

    // Показать модальное окно
    showModal: function (message, options = {}) {
        const defaultOptions = {
            title: 'Внимание!',
            text: message,
            icon: 'warning',
            confirmButtonText: 'OK',
            showCancelButton: false,
            cancelButtonText: 'Отмена'
        };

        return Swal.fire({
            ...defaultOptions,
            ...options
        });
    },

    // Обработка сообщений из AJAX-ответа
    handleAjaxMessages: function (messages) {
        if (Array.isArray(messages)) {
            messages.forEach(message => {
                if (message.extra_tags === 'modal') {
                    this.showModal(
                        message.message,
                        message.modal_options || {}
                    ).then((result) => {
                        if (result.isConfirmed) {
                            // Действия при подтверждении
                            console.log('Confirmed');
                        }
                    });
                } else {
                    this.showToast(message.message, message.level);
                }
            });
        }
    }
};

// Если используете jQuery для AJAX
$(document).ajaxSuccess(function (event, xhr, settings) {
    if (xhr.responseJSON && xhr.responseJSON.messages) {
        MessageManager.handleAjaxMessages(xhr.responseJSON.messages);
    }
});