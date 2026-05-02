frappe.ui.form.on('Smart Chat Settings', {
  knowledge_source_file(frm) {
    if (!frm.doc.knowledge_source_file) return;

    if (frm.is_dirty()) {
      frm.save()
        .then(() => {
          frappe.show_alert({
            message: __('تم حفظ ملف المعرفة على السيرفر بنجاح. يمكنك الآن إعادة بناء فهرس الشات.'),
            indicator: 'green'
          });
          frm.reload_doc();
        })
        .catch(() => {
          frappe.msgprint({
            title: __('فشل حفظ ملف المعرفة'),
            indicator: 'red',
            message: __('تم اختيار الملف لكن لم يُحفَظ في السجل. أعد المحاولة أو اضغط حفظ يدويًا.')
          });
        });
    }
  },

  refresh(frm) {
    if (!frm.doc.knowledge_source_file) {
      frm.dashboard.set_headline_alert(
        __('لم يتم حفظ ملف المعرفة بعد. ارفع ملف Excel/CSV ثم اضغط حفظ قبل إعادة بناء فهرس الشات.')
      );
    } else {
      frm.dashboard.clear_headline();
    }

    frm.add_custom_button(__('فحص إعدادات الشات'), () => {
      frappe.call({
        method: 'aau_university.api.v1.smartchat.inspect_smartchat_source_file',
        freeze: true,
        freeze_message: __('جاري فحص ملف المعرفة على السيرفر...'),
        callback: (response) => {
          const payload = response?.message?.data || {};
          frappe.msgprint({
            title: __('حالة الشات'),
            indicator: payload?.ok ? 'green' : 'orange',
            message: `
              <div>قيمة الحقل: <b>${payload?.hasFieldValue ? __('موجودة') : __('غير موجودة')}</b></div>
              <div>سجل الملف في Frappe: <b>${payload?.hasFileRow ? __('موجود') : __('غير موجود')}</b></div>
              <div>الملف على السيرفر: <b>${payload?.existsOnServer ? __('موجود') : __('غير موجود')}</b></div>
              ${payload?.fileUrl ? `<div style="margin-top:8px">URL: <code>${payload.fileUrl}</code></div>` : ''}
              <div style="margin-top:8px">${payload?.message || ''}</div>
            `
          });
        }
      });
    });

    frm.add_custom_button(__('اختبار الاتصال'), () => {
      frappe.call({
        method: 'aau_university.api.v1.smartchat.test_smartchat_provider',
        freeze: true,
        freeze_message: __('جاري اختبار مزود الشات...'),
        callback: (response) => {
          const message = response?.message?.data || response?.message;
          frappe.msgprint({
            title: __('تم'),
            indicator: 'green',
            message: __('تم اختبار الاتصال بنجاح') + (message?.provider ? `: ${message.provider}` : '')
          });
        }
      });
    });

    frm.add_custom_button(__('إعادة بناء فهرس الشات'), () => {
      if (!frm.doc.knowledge_source_file) {
        frappe.msgprint({
          title: __('ملف المعرفة مفقود'),
          indicator: 'orange',
          message: __('ارفع ملف Excel/CSV في حقل ملف المعرفة ثم اضغط حفظ أولًا.')
        });
        return;
      }
      frappe.call({
        method: 'aau_university.api.v1.smartchat.rebuild_smartchat_index',
        freeze: true,
        freeze_message: __('جاري بناء فهرس الشات من ملف الأسئلة...'),
        callback: (response) => {
          const wrapper = response?.message || {};
          const payload = wrapper?.data || wrapper || {};
          if (wrapper?.ok === false || payload?.ok === false) {
            frappe.msgprint({
              title: __('فشل بناء الفهرس'),
              indicator: 'red',
              message: wrapper?.error?.message || __('تعذر بناء فهرس الشات.')
            });
            return;
          }
          const note = payload?.embeddingSkippedReason ? `<div style="margin-top:8px">${payload.embeddingSkippedReason}</div>` : '';
          frappe.msgprint({
            title: __('تم'),
            indicator: 'green',
            message:
              __('تم تحديث قاعدة معرفة الشات بنجاح') +
              (payload?.count ? ` (${payload.count})` : '') +
              (payload?.searchMode ? ` - ${payload.searchMode}` : '') +
              note
          });
          frm.reload_doc();
        }
      });
    });
  }
});
