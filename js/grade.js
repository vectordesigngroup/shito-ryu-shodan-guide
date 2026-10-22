/* Written-test grader.
   Spelling has to be close, not perfect:
   - case, punctuation, extra spaces and diacritics (macrons) are ignored
   - a listed alternate is accepted
   - each word may differ by a small typo: floor(20% of that word's length),
     and at least 1 character when the word has 4 or more letters
   - the number of words has to match, so Heian #1 does not pass as #2
   Fill-in questions are graded blank by blank. A note of "Any order"
   matches blanks to answers so each answer is used once.
*/
(function (root, factory) {
  var api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  if (root) root.PracticeGrade = api;
})(typeof globalThis !== 'undefined' ? globalThis : this, function () {
  function normalize(value) {
    var t = String(value == null ? '' : value).normalize('NFKD');
    t = t.replace(/\p{M}/gu, '');
    t = t.toLowerCase();
    t = t.replace(/[\u2010\u2011\u2012\u2013\u2014\u2015\u2212\-\/]/g, ' ');
    t = t.replace(/[^\p{L}\p{N}\s]/gu, '');
    t = t.replace(/\s+/g, ' ').trim();
    return t;
  }

  function levenshtein(a, b) {
    if (a === b) return 0;
    var m = a.length;
    var n = b.length;
    if (!m) return n;
    if (!n) return m;
    var prev = new Array(n + 1);
    var cur = new Array(n + 1);
    var i, j, cost, tmp;
    for (j = 0; j <= n; j++) prev[j] = j;
    for (i = 1; i <= m; i++) {
      cur[0] = i;
      var ca = a.charCodeAt(i - 1);
      for (j = 1; j <= n; j++) {
        cost = ca === b.charCodeAt(j - 1) ? 0 : 1;
        var del = prev[j] + 1;
        var ins = cur[j - 1] + 1;
        var sub = prev[j - 1] + cost;
        cur[j] = del < ins ? (del < sub ? del : sub) : (ins < sub ? ins : sub);
      }
      tmp = prev;
      prev = cur;
      cur = tmp;
    }
    return prev[n];
  }

  function typoBudget(length) {
    var len = length | 0;
    var pct = Math.floor(len * 0.2);
    if (len >= 4) return Math.max(1, pct);
    return pct;
  }

  function wordsClose(givenNorm, expectedNorm) {
    if (!givenNorm || !expectedNorm || givenNorm === expectedNorm) return false;
    var gw = givenNorm.split(' ');
    var ew = expectedNorm.split(' ');
    if (gw.length !== ew.length) return false;
    for (var i = 0; i < ew.length; i++) {
      if (gw[i] === ew[i]) continue;
      if (levenshtein(gw[i], ew[i]) > typoBudget(ew[i].length)) return false;
    }
    return true;
  }

  function gradeOne(given, expected, alternates) {
    var raw = given == null ? '' : String(given);
    var canonical = expected == null ? '' : String(expected);
    var g = normalize(raw);
    var e = normalize(canonical);
    var alts = [];
    (alternates || []).forEach(function (alt) {
      if (alt != null && String(alt).trim() !== '') alts.push(String(alt));
    });
    var result = { correct: false, exact: false, close: false, expected: canonical, given: raw };
    if (!g) return result;
    if (e && g === e) {
      result.correct = true;
      result.exact = true;
      return result;
    }
    for (var i = 0; i < alts.length; i++) {
      if (g === normalize(alts[i])) {
        result.correct = true;
        result.close = true;
        return result;
      }
    }
    if (e && wordsClose(g, e)) {
      result.correct = true;
      result.close = true;
      return result;
    }
    for (var k = 0; k < alts.length; k++) {
      var n = normalize(alts[k]);
      if (n && wordsClose(g, n)) {
        result.correct = true;
        result.close = true;
        return result;
      }
    }
    return result;
  }

  function partAlternates(question, part) {
    var list = (part.alternates || []).slice();
    var labels = [normalize(part.label || ''), normalize(part.left || '')].filter(Boolean);
    (question.accepted_alternates || []).forEach(function (alt) {
      var text = String(alt);
      var m = text.match(/^\s*([^:]+):\s*(.+)$/);
      if (!m) return;
      if (labels.indexOf(normalize(m[1])) === -1) return;
      var rest = m[2].replace(/\b(?:also close enough|both accepted)\b/gi, ' ');
      rest.split(/\s*(?:\/|\bOR\b)\s*/i).forEach(function (piece) {
        var p = piece.trim().replace(/^[\s,;]+|[\s,;]+$/g, '');
        if (p) list.push(p);
      });
    });
    return list;
  }

  function isAnyOrder(question) {
    return /any order/i.test(question.note || '');
  }

  function asList(response, n) {
    var arr = Array.isArray(response) ? response.slice(0, n) : [];
    while (arr.length < n) arr.push('');
    return arr.map(function (item) { return item == null ? '' : String(item); });
  }

  function wrap(question, parts) {
    return {
      correct: parts.length > 0 && parts.every(function (p) { return p.correct; }),
      parts: parts,
      answer: question.answer,
      page: question.page,
      note: question.note || ''
    };
  }

  function gradeFill(question, response) {
    var parts = question.parts || [];
    var givens = asList(response, parts.length);
    if (!isAnyOrder(question)) {
      return wrap(question, parts.map(function (part, i) {
        return gradeOne(givens[i], part.answer, partAlternates(question, part));
      }));
    }
    var n = parts.length;
    var m = givens.length;
    var cell = [];
    for (var gi = 0; gi < m; gi++) {
      cell[gi] = [];
      for (var pi = 0; pi < n; pi++) {
        var graded = gradeOne(givens[gi], parts[pi].answer, partAlternates(question, parts[pi]));
        cell[gi][pi] = graded.correct ? graded : null;
      }
    }
    var memo = new Map();
    function dfs(gi, mask) {
      var key = gi * (1 << n) + mask;
      if (memo.has(key)) return memo.get(key);
      if (gi === m) {
        var done = { c: 0, e: 0, a: [] };
        memo.set(key, done);
        return done;
      }
      var skipped = dfs(gi + 1, mask);
      var bestC = skipped.c;
      var bestE = skipped.e;
      var bestA = [-1].concat(skipped.a);
      for (var p = 0; p < n; p++) {
        if (mask & (1 << p)) continue;
        if (!cell[gi][p]) continue;
        var sub = dfs(gi + 1, mask | (1 << p));
        var c = sub.c + 1;
        var e = sub.e + (cell[gi][p].exact ? 1 : 0);
        if (c > bestC || (c === bestC && e > bestE)) {
          bestC = c;
          bestE = e;
          bestA = [p].concat(sub.a);
        }
      }
      var res = { c: bestC, e: bestE, a: bestA };
      memo.set(key, res);
      return res;
    }
    var best = n > 16 ? { c: 0, a: givens.map(function () { return -1; }) } : dfs(0, 0);
    var gradedParts = givens.map(function (given, gi) {
      var pi = best.a[gi];
      if (pi == null || pi < 0) {
        return { correct: false, exact: false, close: false, expected: '', given: given };
      }
      return cell[gi][pi];
    });
    var out = wrap(question, gradedParts);
    out.correct = n > 0 && m === n && best.c === n;
    return out;
  }

  function letterOf(given) {
    var s = String(given || '').trim();
    if (/^[A-Za-z]$/.test(s)) return s.toUpperCase();
    var m = s.match(/^([A-Za-z])\s*[.)](?:\s|$)/);
    return m ? m[1].toUpperCase() : '';
  }

  function gradeMatch(question, response) {
    var pairs = question.pairs || [];
    var givens = asList(response, pairs.length);
    var parts = pairs.map(function (pair, i) {
      var given = givens[i];
      var expectedLetter = String(pair.letter || '').toUpperCase();
      var expected = expectedLetter + '. ' + pair.right;
      var letter = letterOf(given);
      if (letter && letter === expectedLetter) {
        return { correct: true, exact: true, close: false, expected: expected, given: given };
      }
      var text = gradeOne(given, pair.right, partAlternates(question, pair));
      if (text.correct) {
        text.expected = pair.right;
        return text;
      }
      return { correct: false, exact: false, close: false, expected: expected, given: given };
    });
    return wrap(question, parts);
  }

  function gradeScalar(question, response) {
    var given = Array.isArray(response) ? response[0] : response;
    return wrap(question, [gradeOne(given, question.answer, question.accepted_alternates || [])]);
  }

  function gradeQuestion(question, response) {
    if (!question || !question.type) throw new Error('question required');
    if (question.type === 'short' || question.type === 'mc') return gradeScalar(question, response);
    if (question.type === 'fill') return gradeFill(question, response);
    if (question.type === 'match') return gradeMatch(question, response);
    throw new Error('unknown question type');
  }

  return {
    normalize: normalize,
    levenshtein: levenshtein,
    typoBudget: typoBudget,
    gradeOne: gradeOne,
    gradeQuestion: gradeQuestion,
    letterOf: letterOf
  };
});
