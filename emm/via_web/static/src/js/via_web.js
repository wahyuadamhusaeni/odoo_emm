openerp.via_web = function(openerp) {

    // This method is copied from underscore.string VERSION 2.3.2
    // OpenERP 7.0 uses older version of underscore.string (VERSION 1.2.0)
    // that does not yet provide this function.

    var numberFormat = function(number, dec, dsep, tsep) {
      if (isNaN(number) || number == null) return '';

      number = number.toFixed(~~dec);
      tsep = typeof tsep == 'string' ? tsep : ',';

      var parts = number.split('.'), fnums = parts[0],
        decimals = parts[1] ? (dsep || '.') + parts[1] : '';

      return fnums.replace(/(\d)(?=(?:\d{3})+$)/g, '$1' + tsep) + decimals;
    };

    _.str.numberFormat = numberFormat;
    _.string.numberFormat = numberFormat;

    openerp.web.UserMenu =  openerp.web.UserMenu.extend({
        on_menu_infinity: function() {
            window.open('http://www.infi-nity.com', '_blank');
        },
    });

    openerp.web.WebClient = openerp.web.WebClient.extend({
        init: function() {
            this._super.apply(this, arguments);
            this.set_title();
        },
        set_title: function(title) {
            title = _.str.clean(title);
            var sep = _.isEmpty(title) ? '' : ' - ';
            document.title = title + sep + 'infinity';
        },
    });

    // This is a replacement hack of the original load_js function that belongs to
    // instance.web.Session in Client Web's addons/web/static/src/js/coresetup.js
    // The purpose is to reload /web/static/lib/datejs/parser.js in order to get the
    // parser's CultureInfo properly set.
    //
    // Originally /web/static/lib/datejs/parser.js is called after
    // /web/static/lib/datejs/globalization/en-US.js by way of Client Web's web module
    // __openerp__.py (which is rendered by Client Web's /addons/web/controllers/main.py
    // Home Class index method).  This causes the instantiated parser to have en_US
    // CultureInfo regardless of user's Language setting
    //
    // This hack call and re-instantiate the parser after the Date's CultureInfo
    // is set with user's Language setting.
    //
    // This is a replacement hack, meaning it replaceses the original load_js function
    // in entirety.  Thus care must be taken to sync this with the latest load_js
    // function.
    // TODO: Sync with latest load_js function.

    openerp.web.Session.prototype.load_js = function(files) {
            // Reinstantiate parser.js if a new CultureInfo is set
            // CultureInfos are stored in /web/static/lib/datejs/globalization/ folder
            for(var i=0; i<files.length; ++i) {
                if (files[i].indexOf('/web/static/lib/datejs/globalization/') != -1) {
                    files.push('/web/static/lib/datejs/parser.js');
                }
            }

            // From here to the end of the function is the original load_js function
            var self = this;
            var d = $.Deferred();
            if(files.length !== 0) {
                var file = files.shift();
                var tag = document.createElement('script');
                tag.type = 'text/javascript';
                tag.src = self.url(file, null);
                tag.onload = tag.onreadystatechange = function() {
                    if ( (tag.readyState && tag.readyState != "loaded" && tag.readyState != "complete") || tag.onload_done )
                        return;
                    tag.onload_done = true;
                    self.load_js(files).done(function () {
                        d.resolve();
                    });
                };
                var head = document.head || document.getElementsByTagName('head')[0];
                head.appendChild(tag);
            } else {
                d.resolve();
            }
            return d;
        };
}
