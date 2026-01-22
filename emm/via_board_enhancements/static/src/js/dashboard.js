openerp.via_board_enhancements = function(instance) {
    instance.web.form.DashBoard = instance.web.form.DashBoard.extend({

        // This is a override of the original method defined in
        // board/static/src/js/dashboard.js
        // TODO: Need to sync this with the updated version

        on_load_action: function(result, index, action_attrs) {
            var self = this,
                action = result,
                view_mode = action_attrs.view_mode;

            // evaluate action_attrs context and domain
            action_attrs.context_string = action_attrs.context;
            action_attrs.context = instance.web.pyeval.eval(
                'context', action_attrs.context || {});
            action_attrs.domain_string = action_attrs.domain;
            action_attrs.domain = instance.web.pyeval.eval(
                'domain', action_attrs.domain || [], action_attrs.context);
            if (action_attrs.context['dashboard_merge_domains_contexts'] === false) {
                // TODO: replace this 6.1 workaround by attribute on <action/>
                action.context = action_attrs.context || {};
                action.domain = action_attrs.domain || [];
            } else {
                action.context = instance.web.pyeval.eval(
                    'contexts', [action.context || {}, action_attrs.context]);
                action.domain = instance.web.pyeval.eval(
                    'domains', [action_attrs.domain, action.domain || []],
                    action.context)
            }

            var action_orig = _.extend({ flags : {} }, action);

            if (view_mode && view_mode != action.view_mode) {
                action.views = _.map(view_mode.split(','), function(mode) {
                    mode = mode === 'tree' ? 'list' : mode;
                    return _(action.views).find(function(view) { return view[1] == mode; })
                        || [false, mode];
                });
            }

            // TODO: The change from the original module is pager set to true instead of false
            action.flags = {
                search_view : false,
                sidebar : false,
                views_switcher : false,
                action_buttons : false,
                pager: true,
                low_profile: true,
                display_title: false,
                list: {
                    selectable: false
                }
            };
            var am = new instance.web.ActionManager(this),
                // FIXME: ideally the dashboard view shall be refactored like kanban.
                $action = $('#' + this.view.element_id + '_action_' + index);
            $action.parent().data('action_attrs', action_attrs);
            this.action_managers.push(am);
            am.appendTo($action);
            am.do_action(action);
            am.do_action = function (action) {
                self.do_action(action);
            };
            if (am.inner_widget) {
                var new_form_action = function(id, editable) {
                    var new_views = [];
                    _.each(action_orig.views, function(view) {
                        new_views[view[1] === 'form' ? 'unshift' : 'push'](view);
                    });
                    if (!new_views.length || new_views[0][1] !== 'form') {
                        new_views.unshift([false, 'form']);
                    }
                    action_orig.views = new_views;
                    action_orig.res_id = id;
                    action_orig.flags = {
                        form: {
                            "initial_mode": editable ? "edit" : "view",
                        }
                    };
                    self.do_action(action_orig);
                };
                var list = am.inner_widget.views.list;
                if (list) {
                    list.deferred.done(function() {
                        $(list.controller.groups).off('row_link').on('row_link', function(e, id) {
                            new_form_action(id);
                        });
                    });
                }
                var kanban = am.inner_widget.views.kanban;
                if (kanban) {
                    kanban.deferred.done(function() {
                        kanban.controller.open_record = function(id, editable) {
                            new_form_action(id, editable);
                        };
                    });
                }
            }
        },
    });
};
