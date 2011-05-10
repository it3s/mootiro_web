/*!
 * Transecma, a javaScript i18n library v0.1
 * http://github.com/it3s/mootiro_web
 *
 * Copyright 2011, Nando Florestan
 *
 * Usage:

// The input is a translation map such as
translationsObject = {
    'I think we must review our processes.':
        'Who the hell was so stupid as to cause this #$%&*???',
    "If you don't know why I'm mad at you, do you think I'm going to tell you?":
        "I am your girlfriend and I am extremely anxious!",
    'I came, I saw, I conquered!': 'Veni, vidi, vici!',
    'Item {0} of {1}':
        'We have {1} items (really, {1}) and this is item number {0}.'
}
localizer = Transecma(translationsObject);
// We recommend these 3 nicknames for the translator function:
gettext = tr = _ = localizer.translate;
// Here are some demonstrations:
tests = [
    _('I came, I saw, I conquered!'),
    _('Item {0} of {1}').interpol(8, 9)
];
alert(tests.join('\n'));

*/

String.prototype.interpol = function () {
    // String interpolation for format strings like "Item {0} of {1}".
    // May receive strings or numbers as arguments.
    // For usage, see the test function below.
    var args = arguments;
    try {
        return this.replace(/\{(\d+)\}/g, function () {
            // The replacement string is given by the nth element in the list,
            // where n is the second group of the regular expression:
            return args[arguments[1]];
        });
    } catch (e) {
        if (window.console) console.log(['Exception on interpol() called on',
            this, 'with arguments', arguments]);
        throw(e);
    }
}
String.prototype.interpol.test = function() {
    if ('Item #{0} of {1}. Really, item {0}.'.interpol(5, 7)
        != "Item #5 of 7. Really, item 5.")  throw('Blimey -- oh no!');
}


function Transecma(tt) {
    // The argument must be a dictionary containing the translations.
    o = {
        translate: function (msg1, msg2, n) {
            if (!n || n == 1)
                var s = new String(tt[msg1] || msg1);
            else
                var s = new String(tt[msg2] || msg2);
            // I created a new String because now I add a few attributes
            s.singular = msg1;
            s.plural = msg2;
            s.n = n;
            return s;
        }
    };
    return o;
}
