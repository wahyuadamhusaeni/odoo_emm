
openerp.emm_stock_enhancements = function (instance) {
    // this module interfaces with the barcode reader. It assumes the barcode reader
    // is set-up to act like  a keyboard. Use connect() and disconnect() to activate
    // and deactivate the barcode reader.
    instance.BarcodeReader = instance.web.Class.extend({
        init: function (attributes) {
            this.view = attributes.view;
        },

        on_barcode: function (barcode) {
            // Callback the name search of the entered barcode and call the hook method of the class
            var self = this.view;
            var srcElement = this.handler.arguments[0].target.tagName
            if ((self.dataset.model == 'stock.picking.out') && (self.view_type == 'form') && (srcElement == 'BODY')) {
                var _data = self.dataset._model.call('validate_serial_number', [[self.datarecord.id], barcode]).done(function(data) {
                    self.reload();
                });
            }
            if ((self.dataset.model == 'stock.picking') && (self.view_type == 'form') && (srcElement == 'BODY')) {
                var _data = self.dataset._model.call('add_move_lines', [[self.datarecord.id], barcode]).done(function(data) {
                    self.reload();
                });
            }
        },

        // starts catching keyboard events and tries to interpret codebar
        // calling the callbacks when needed.
        connect: function () {
            var self = this;
            var codeNumbers = [];
            var keyCodes = [];      // Debugging variable to see what KeyCodes are collected
            var codeString = [];    // Debugging variable to see what strings are collected
            var timeStamp = 0;
            var lastTimeStamp = 0;

            // The barcode readers acts as a keyboard, we catch all keyPress events and try to find a
            // barcode sequence in the typed keys, then act accordingly.
            // Event handler behaviour differs in various browsers.  The currently tested acceptable
            // method is to use keyPress (instead of keyUp or keyDown) and capture the charCode which
            // will be an ASCII code of the character being written.  Other non alpha-numeric keys
            // (such as Enter) need to be captured using keyCode, hence the different attributes used
            // in the first 2 branches of if below
            this.handler = function(e){
                // Provide a more generic barcode handler, capable of alpha-numeric
                if (e.charCode >= 32 && e.charCode <= 126) {
                    // The barcode reader sends keystrokes with a specific interval.
                    // We look if the typed keys fit in the interval.
                    if (codeNumbers.length === 0) {
                        timeStamp = new Date().getTime();
                    } else {
                        if (lastTimeStamp + 500 < new Date().getTime()) {
                            // Not a barcode reader
                            console.log("Resetting due to timestamp");
                            timeStamp = new Date().getTime();
                            codeNumbers = [];
                            keyCodes = [];
                            codeString = [];
                        }
                    }
                    codeNumbers.push(String.fromCharCode(e.charCode));
                    lastTimeStamp = new Date().getTime();
                } else if (e.keyCode == 13) {
                    // console.log(keyCodes);
                    // console.log(codeString);
                    // console.log(codeNumbers);

                    self.on_barcode(codeNumbers.join(''));
                    codeNumbers = [];
                } else {
                    // Unrecognizable code, just drop it
                    // Data Link Escape character (keyCode 16) often is wedged within the sent character
                }
                // console.log(e.keyCode);
                // console.log(String.fromCharCode(e.keyCode));
                // console.log(e.charCode);
                // console.log(String.fromCharCode(e.charCode));
                // console.log(e.which);
                // console.log(String.fromCharCode(e.which));
                // console.log(codeNumbers);
            };
            $('body').on('keypress', this.handler);
        },


        // stops catching keyboard events
        disconnect: function () {
            $('body').off('keypress', this.handler);
        }
    });

    instance.web.FormView = instance.web.FormView.extend({
        load_form: function(data) {
            this._super.apply(this, arguments);
            if ((this.ViewManager.active_view) && (this.model == 'stock.picking.out')) {
                this.barcode_reader = new instance.BarcodeReader({'view': this});
                this.barcode_reader.connect();
            }
            if ((this.ViewManager.active_view) && (this.model == 'stock.picking')) {
                this.barcode_reader = new instance.BarcodeReader({'view': this});
                this.barcode_reader.connect();
            }
        },
        destroy: function() {
            if (this.barcode_reader) {
                this.barcode_reader.disconnect();
            }
            this._super.apply(this, arguments);
        }
    });
};
