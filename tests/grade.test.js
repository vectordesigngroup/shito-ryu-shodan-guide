const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const G = require('../js/grade.js');

const data = JSON.parse(fs.readFileSync(path.join(__dirname, '../data/practice-test.json'), 'utf8'));
const questions = data.questions;

function q(id) {
  return questions.find(function (item) { return item.id === id; });
}

function official(question) {
  if (question.type === 'short' || question.type === 'mc') return question.answer;
  if (question.type === 'fill') return question.parts.map(function (part) { return part.answer; });
  if (question.type === 'match') return question.pairs.map(function (pair) { return pair.letter; });
  throw new Error('type');
}

test('normalize ignores case, punctuation, extra spaces, slashes and macrons', function () {
  assert.equal(G.normalize('  Empty   hand!! '), 'empty hand');
  assert.equal(G.normalize('Shito-Ryu'), 'shito ryu');
  assert.equal(G.normalize('Shito—Ryu'), 'shito ryu');
  assert.equal(G.normalize('"X" stance'), 'x stance');
  assert.equal(G.normalize("you're"), 'youre');
  assert.equal(G.normalize('Shin/foot guards'), 'shin foot guards');
  assert.equal(G.normalize('Peaceful mind #1'), 'peaceful mind 1');
  assert.equal(G.normalize('Zanshin (perfect finish)'), 'zanshin perfect finish');
  assert.equal(G.normalize('Explanation & application'), 'explanation application');
  assert.equal(G.normalize('Ōkinawa'), 'okinawa');
  assert.equal(G.normalize('ū'), 'u');
  assert.equal(G.normalize('Ā'), 'a');
});

test('typo budget is 20% and at least 1 for words of 4+ letters', function () {
  assert.equal(G.typoBudget(0), 0);
  assert.equal(G.typoBudget(1), 0);
  assert.equal(G.typoBudget(3), 0);
  assert.equal(G.typoBudget(4), 1);
  assert.equal(G.typoBudget(5), 1);
  assert.equal(G.typoBudget(9), 1);
  assert.equal(G.typoBudget(10), 2);
  assert.equal(G.typoBudget(14), 2);
  assert.equal(G.typoBudget(15), 3);
  assert.equal(G.typoBudget(20), 4);
  assert.equal(G.levenshtein('kitten', 'sitting'), 3);
  assert.equal(G.levenshtein('karate', 'karat'), 1);
  assert.equal(G.levenshtein('', 'a'), 1);
});

test('short answers: exact, close, alternate and rejected typos', function () {
  var karate = G.gradeQuestion(q(1), 'Karat');
  assert.equal(karate.correct, true);
  assert.equal(karate.parts[0].close, true);
  assert.equal(karate.parts[0].expected, 'Karate');
  assert.equal(G.gradeQuestion(q(1), 'Kart').correct, false);
  assert.equal(G.gradeQuestion(q(1), 'KARATE').parts[0].exact, true);
  assert.equal(G.gradeQuestion(q(1), '   ').correct, false);

  var oki = G.gradeQuestion(q(4), 'Ōkinawa');
  assert.equal(oki.correct, true);
  assert.equal(oki.parts[0].exact, true);
  assert.equal(oki.parts[0].close, false);

  var shito = G.gradeQuestion(q(5), 'Shito Ryu');
  assert.equal(shito.parts[0].exact, true);
  var glued = G.gradeQuestion(q(5), 'Shitoryu');
  assert.equal(glued.correct, true);
  assert.equal(glued.parts[0].close, true);

  assert.equal(G.gradeQuestion(q(26), 'Explaination & application').parts[0].close, true);
  assert.equal(G.gradeQuestion(q(26), 'Explanation and application').correct, false);
  assert.equal(G.gradeQuestion(q(45), '3').parts[0].close, true);
  assert.equal(G.gradeQuestion(q(45), 'THREE').parts[0].exact, true);

  var motions = G.gradeQuestion(q(22), 'up out bak down');
  assert.equal(motions.correct, true);
  assert.equal(motions.parts[0].close, true);
  assert.equal(G.gradeQuestion(q(22), 'up out down back').correct, false);
});

test('near misses that change the meaning stay wrong', function () {
  assert.equal(G.gradeOne('Outside', 'Inside', []).correct, false);
  assert.equal(G.gradeOne('Left', 'Right', []).correct, false);
  assert.equal(G.gradeOne('Chi', 'Shi', []).correct, false);
  assert.equal(G.gradeOne('Goo', 'Go', []).correct, false);
  assert.equal(G.gradeOne('Head', 'Hand', []).correct, false);
  assert.equal(G.gradeOne('Blue', 'Black', []).correct, false);
  assert.equal(G.gradeOne('Jyo', 'Jyu', []).correct, false);
});

test('fill blanks grade separately, including any-order and listed alternates', function () {
  var regions = q(8);
  assert.equal(G.gradeQuestion(regions, ['Tomari', 'Naha', 'Shuri']).correct, true);
  var partial = G.gradeQuestion(regions, ['Naha', 'Shuri', 'Nope']);
  assert.equal(partial.correct, false);
  assert.equal(partial.parts.filter(function (p) { return p.correct; }).length, 2);

  var virtues = q(17);
  var reversed = virtues.parts.map(function (p) { return p.answer; }).reverse();
  assert.equal(G.gradeQuestion(virtues, reversed).correct, true);
  assert.equal(G.gradeQuestion(virtues, ['Courage', 'Courage', 'Integrity', 'Humility', 'Self-Control']).correct, false);

  var rules = q(21);
  assert.equal(G.gradeQuestion(rules, rules.parts.map(function (p) { return p.answer; }).reverse()).correct, false);

  var styles = q(9);
  assert.equal(G.gradeQuestion(styles, ['Wado-Ryu', 'Goju-Ryu', 'Shotokan', 'Shito Ryu']).correct, true);

  var founders = q(10);
  var founderAnswers = founders.parts.map(function (p) { return p.answer; });
  founderAnswers[2] = 'Hironori Ōtsuka';
  var founderGrade = G.gradeQuestion(founders, founderAnswers);
  assert.equal(founderGrade.correct, true);
  assert.equal(founderGrade.parts[2].close, true);
  assert.equal(founderGrade.parts[2].expected, 'Hironori Ohtsuka');

  var numbers = q(51);
  var ju = numbers.parts.map(function (p) { return p.answer; });
  ju[9] = 'Ju';
  var juGrade = G.gradeQuestion(numbers, ju);
  assert.equal(juGrade.correct, true);
  assert.equal(juGrade.parts[9].close, true);
  assert.equal(juGrade.parts[9].expected, 'Jyu');
  ju[9] = 'Juu';
  assert.equal(G.gradeQuestion(numbers, ju).parts[9].correct, true);
  ju[9] = 'Jyo';
  assert.equal(G.gradeQuestion(numbers, ju).correct, false);

  var take = q(35);
  var takeAnswers = take.parts.map(function (p) { return p.answer; });
  takeAnswers[2] = 'Naga Waza';
  assert.equal(G.gradeQuestion(take, takeAnswers).parts[2].correct, true);
});

test('kata order matters and a different number is not a typo', function () {
  var kata = q(54);
  assert.equal(G.gradeQuestion(kata, official(kata)).correct, true);
  assert.equal(G.gradeQuestion(kata, official(kata).slice().reverse()).correct, false);
  var swapped = official(kata);
  swapped[4] = 'Heian Shodan: Peaceful mind #2 kata';
  assert.equal(G.gradeQuestion(kata, swapped).parts[4].correct, false);
  swapped[4] = 'Peaceful mind #1';
  var alt = G.gradeQuestion(kata, swapped);
  assert.equal(alt.parts[4].correct, true);
  assert.equal(alt.parts[4].close, true);
  assert.equal(alt.correct, true);
  var long = q(16);
  var sentence = long.parts.map(function (p) { return p.answer; });
  sentence[2] = 'Never use your karate on anyone unless youre defending youself';
  assert.equal(G.gradeQuestion(long, sentence).parts[2].close, true);
  sentence[2] = 'Never use your karate unless you are defending yourself';
  assert.equal(G.gradeQuestion(long, sentence).parts[2].correct, false);
});

test('matching uses the letter and multiple choice uses the option', function () {
  var stances = q(28);
  assert.equal(G.gradeQuestion(stances, official(stances)).correct, true);
  var wrong = official(stances);
  wrong[0] = 'a';
  assert.equal(G.gradeQuestion(stances, wrong).correct, false);
  assert.equal(G.gradeQuestion(stances, official(stances).map(function (letter) { return letter.toLowerCase(); })).correct, true);

  var body = q(46);
  var ashi = body.pairs.findIndex(function (pair) { return pair.left === 'Ashi'; });
  var foot = official(body);
  foot[ashi] = 'leg';
  var footGrade = G.gradeQuestion(body, foot);
  assert.equal(footGrade.parts[ashi].correct, true);
  assert.equal(footGrade.parts[ashi].close, true);
  assert.equal(footGrade.correct, true);
  foot[ashi] = 'hand';
  assert.equal(G.gradeQuestion(body, foot).parts[ashi].correct, false);

  questions.filter(function (item) { return item.type === 'mc'; }).forEach(function (item) {
    assert.equal(item.options.indexOf(item.answer) !== -1, true);
    assert.equal(G.gradeQuestion(item, item.answer).parts[0].exact, true);
    var other = item.options.find(function (opt) { return opt !== item.answer; });
    assert.equal(G.gradeQuestion(item, other).correct, false);
  });
});

test('every official answer passes and a blank answer fails', function () {
  assert.equal(data.meta.question_count, 59);
  assert.equal(questions.length, 59);
  var ids = questions.map(function (item) { return item.id; });
  assert.deepEqual(ids, Array.from({ length: 59 }, function (_, i) { return i + 1; }));
  questions.forEach(function (item) {
    assert.equal(typeof item.prompt, 'string');
    assert.equal(typeof item.answer, 'string');
    assert.ok(Array.isArray(item.accepted_alternates));
    var graded = G.gradeQuestion(item, official(item));
    assert.equal(graded.correct, true, 'official answer failed for ' + item.id);
    var blank = item.type === 'short' || item.type === 'mc' ? '' : official(item).map(function () { return ''; });
    assert.equal(G.gradeQuestion(item, blank).correct, false, 'blank passed for ' + item.id);
    if (item.type === 'fill') {
      item.parts.forEach(function (part, index) {
        (part.alternates || []).forEach(function (alt) {
          var resp = official(item).slice();
          resp[index] = alt;
          assert.equal(G.gradeQuestion(item, resp).parts[index].correct, true, item.id + ' alt ' + alt);
        });
      });
    }
  });
});
