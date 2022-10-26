var express = require('express');
var router = express.Router();
var db = require('./db.js');
var $ = require('jquery');

/* GET ducks route */
router.get('/', function(req, res, next) {
	db.getDuckPlusData().then((ducks) => {
		res.render('ducks',
		{
			title: 'Express',
			something: ducks
		});
		// console.log(ducks)

	});
  //res.render('ducks', { title: 'Express' });

});

router.get('/getAllData', function (req, res, next) {
  db.getAllData().then((response) => {
    console.log(response);

    res.json(response);
  });
});

router.get('/getDataByDuckId/:duckId', function (req, res, next) {
  db.getDataByDuckId(req.params.duckId).then((response) => {
    console.log(response);

    res.json(response);
  });
});

router.get('/getUniqueDucks', function (req, res, next) {
  db.getUniqueDucks().then((response) => {
    console.log(response);

    res.json(response);



  });
});

router.get('/getLastCount/:count', function (req, res, next) {
  db.getLastCount(req.params.count).then((response) => {
    console.log(response);

    res.json(response);

  });
});

router.post('/postEnableWiFi', function (req, res) {
  db.postCommand(" /wifi/", "1" + String(req.body.duck_id));
  res.redirect('/ducks');
});

router.post('/postDisableWiFi', function (req, res) {
  db.postCommand(" /wifi/", "0" + String(req.body.duck_id));
  res.redirect('/ducks');
});


new Date().toLocaleString()





module.exports = router;
