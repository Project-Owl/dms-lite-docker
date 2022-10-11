var createError = require('http-errors');
var express = require('express');
var path = require('path');
var cookieParser = require('cookie-parser');
var logger = require('morgan');

var indexRouter = require('./routes/index');
var usersRouter = require('./routes/users');
var dataRouter = require('./routes/data');
var ducksRouter = require('./routes/ducks');
var settingsRouter = require('./routes/settings');
var dbRouter = require('./routes/db')


var app = express();


// view engine setup
app.set('views', path.join(__dirname, 'views'));
app.set('view engine', 'ejs');

app.use(logger('dev'));
app.use(express.json());
app.use(express.urlencoded({ extended: false }));
app.use(cookieParser());
app.use(express.static(path.join(__dirname, 'public')));
app.use('/jquery', express.static(__dirname + '/node_modules/jquery/dist/'));

app.use('/', indexRouter);
app.use('/users', usersRouter);
app.use('/data', dataRouter);
app.use('/settings', settingsRouter);
app.use('/ducks', ducksRouter);

// Serve libraries that were installed via npm - thanks to https://stackoverflow.com/a/70744989
app.use('/stylesheets/leaflet/', express.static(path.join(__dirname, "node_modules/leaflet/dist/")));
app.use('/stylesheets/bootstrap/', express.static(path.join(__dirname, "node_modules/bootstrap/dist/")));
app.use('/stylesheets/tablefilter/', express.static(path.join(__dirname, "node_modules/leaflet/dist/")));
app.use('/scripts/chart.js/', express.static(path.join(__dirname, "node_modules/chart.js/dist/chart.js/")));
app.use('/scripts/chart.esm.js/', express.static(path.join(__dirname, "node_modules/chart.js/dist/helper.esm.js/")));

app.get("/", (req, res) => {
  // check if user is logged in, by checking cookie
  let detailedView = req.cookies.detailedView;

  // render the home page
  return res.render("data", {
    detailedView,
  });
});
app.listen(8000, () => console.log('The server is running port 3000...'));

app.get("/settings", (req, res) => {
  // get the username
  let detailedView = req.cookies.username;

  // render welcome page
  return res.render("settings", {
    detailedView,
  });
});

app.get("/data", (req, res) => {
  // get the username
  let detailedView = req.cookies.detailedView;

  // render welcome page
  return res.render("data", {
    detailedView,
  });
});

app.get('/getcookie', (req, res) => {
  // show the saved cookies
  console.log(req.cookies)
  res.send(req.cookies);
});

app.post("/save", (req, res) => {
  // get the data
  let { detailedView } = req.body;
  console.log(req.body.toString())
  // saving the data to the cookies
  res.cookie("detailedView", detailedView);
  // redirect
  return res.redirect("/data");//settings

});


// catch 404 and forward to error handler
app.use(function(req, res, next) {
  next(createError(404));
});

// error handler
app.use(function(err, req, res, next) {
  // set locals, only providing error in development
  res.locals.message = err.message;
  res.locals.error = req.app.get('env') === 'development' ? err : {};

  // render the error page
  res.status(err.status || 500);
  res.render('error');
});

module.exports = app;
