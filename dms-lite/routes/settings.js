var express = require('express');
var router = express.Router();

/* GET settings route */
router.get('/', function(req, res, next) {
  res.render('settings', { title: 'Express', cookies: req.cookies });
});

const cookieparser = require("cookie-parser");
router.use(cookieparser());

module.exports = router;
