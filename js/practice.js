(function () {
  var KEY = 'katsu-practice-test-v1';
  var G = window.PracticeGrade;
  var app = document.getElementById('pt-app');
  if (!app) return;

  var bank = [];
  var state = { missed: [], session: null };
  var confirmReset = false;

  function questionsById(id) {
    for (var i = 0; i < bank.length; i++) if (bank[i].id === id) return bank[i];
    return null;
  }

  function sections() {
    var out = [];
    bank.forEach(function (q) {
      if (out.indexOf(q.section) === -1) out.push(q.section);
    });
    return out;
  }

  function sectionCount(name) {
    return bank.filter(function (q) { return q.section === name; }).length;
  }

  function load() {
    state = { missed: [], session: null };
    try {
      var raw = JSON.parse(localStorage.getItem(KEY) || 'null');
      if (!raw || typeof raw !== 'object') return;
      var known = {};
      bank.forEach(function (q) { known[q.id] = true; });
      if (Array.isArray(raw.missed)) {
        state.missed = raw.missed.filter(function (id) { return known[id]; });
      }
      if (raw.session && Array.isArray(raw.session.ids)) {
        var ids = raw.session.ids.filter(function (id) { return known[id]; });
        if (ids.length) {
          state.session = raw.session;
          state.session.ids = ids;
          if (!state.session.results || typeof state.session.results !== 'object') state.session.results = {};
          if (state.session.index >= ids.length) state.session.phase = 'results';
        }
      }
    } catch (e) {
      state = { missed: [], session: null };
    }
  }

  function save() {
    try {
      localStorage.setItem(KEY, JSON.stringify({ missed: state.missed, session: state.session }));
    } catch (e) {}
  }

  function el(tag, cls, text) {
    var node = document.createElement(tag);
    if (cls) node.className = cls;
    if (text != null) node.textContent = text;
    return node;
  }

  function hasKanji(text) {
    return /[\u3400-\u9fff]/.test(text || '');
  }

  function formatPages(page) {
    var pages = (Array.isArray(page) ? page : [page]).filter(function (p) { return p != null && p !== ''; });
    if (!pages.length) return '';
    if (pages.length === 1) return 'Manual p. ' + pages[0];
    return 'Manual pp. ' + pages.join(', ');
  }

  function percent(correct, total) {
    if (!total) return 0;
    return Math.round(correct / total * 100);
  }

  function scoreOf(session) {
    var answered = 0;
    var correct = 0;
    (session.ids || []).forEach(function (id) {
      var result = session.results[id] || session.results[String(id)];
      if (!result) return;
      answered++;
      if (result.correct) correct++;
    });
    return { answered: answered, correct: correct, total: session.ids.length };
  }

  function resultFor(session, id) {
    return session.results[id] || session.results[String(id)] || null;
  }

  function shuffle(ids) {
    var a = ids.slice();
    for (var i = a.length - 1; i > 0; i--) {
      var j = Math.floor(Math.random() * (i + 1));
      var t = a[i];
      a[i] = a[j];
      a[j] = t;
    }
    return a;
  }

  function modeLabel(session) {
    if (session.mode === 'shuffle') return 'Shuffled';
    if (session.mode === 'section') return session.section || 'Section';
    if (session.mode === 'missed') return 'Missed questions';
    return 'In order';
  }

  function clear(node) {
    while (node.firstChild) node.removeChild(node.firstChild);
  }

  function button(label, act, extra) {
    var b = el('button', extra || '', label);
    b.type = 'button';
    b.setAttribute('data-act', act);
    return b;
  }

  function renderMenu() {
    clear(app);
    var intro = el('p', 'muted', 'Written exam practice from the Katsu Dojo Digital Textbook, Part Six (printed pages 115–129). The written test needs 100%. Spelling only has to be close: capitalization, punctuation and small typos are forgiven. Check each answer as you go. Progress stays in this browser.');
    app.appendChild(intro);
    app.appendChild(el('p', 'muted', bank.length + ' questions. Nothing is sent anywhere.'));

    var session = state.session;
    if (session && session.ids && session.ids.length) {
      var sc = scoreOf(session);
      if (session.phase === 'results') {
        app.appendChild(el('p', '', 'Last test: ' + sc.correct + ' / ' + sc.total + ' (' + percent(sc.correct, sc.total) + '%).'));
        app.appendChild(button('View results', 'results'));
      } else {
        var at = Math.min(session.index + 1, session.ids.length);
        app.appendChild(el('p', '', 'Saved test (' + modeLabel(session) + '): question ' + at + ' of ' + session.ids.length + '. Score ' + sc.correct + ' / ' + sc.answered + '.'));
        app.appendChild(button('Continue', 'continue'));
      }
    }

    var modes = el('div', 'pt-modes');
    modes.appendChild(button('Full test, in order', 'order'));
    modes.appendChild(button('Shuffled', 'shuffle'));
    var row = el('div', 'pt-section-row');
    var sel = el('select');
    sel.id = 'pt-section';
    sel.setAttribute('aria-label', 'Section');
    sections().forEach(function (name) {
      var opt = el('option', '', name + ' (' + sectionCount(name) + ')');
      opt.value = name;
      sel.appendChild(opt);
    });
    row.appendChild(sel);
    row.appendChild(button('Start section', 'section'));
    modes.appendChild(row);

    var missedN = state.missed.length;
    var retry = button('Retry missed only (' + missedN + ')', 'missed', 'g');
    retry.disabled = missedN === 0;
    if (!missedN) retry.title = 'No missed questions yet';
    modes.appendChild(retry);

    if (!confirmReset) {
      modes.appendChild(button('Reset progress', 'reset-ask', 'g'));
    } else {
      var ask = el('div', 'pt-confirm');
      ask.appendChild(el('p', '', 'Reset clears the saved test and the missed-question list.'));
      var askRow = el('div', 'pt-actions');
      askRow.appendChild(button('Reset progress', 'reset-do'));
      askRow.appendChild(button('Cancel', 'reset-no', 'g'));
      ask.appendChild(askRow);
      modes.appendChild(ask);
    }
    app.appendChild(modes);
    if (session && session.phase !== 'results') {
      app.appendChild(el('p', 'muted', 'Starting a new test replaces the one in progress. Questions already marked missed stay on the missed list until you get them right or reset.'));
    }
  }

  function progressBlock(session) {
    var sc = scoreOf(session);
    var wrap = el('div', 'pt-progress');
    var bar = el('div', 'pt-bar');
    bar.setAttribute('role', 'progressbar');
    bar.setAttribute('aria-valuemin', '0');
    bar.setAttribute('aria-valuemax', String(sc.total));
    bar.setAttribute('aria-valuenow', String(sc.answered));
    bar.setAttribute('aria-label', 'Questions answered');
    var fill = el('span');
    fill.style.width = (sc.total ? (sc.answered / sc.total * 100) : 0) + '%';
    bar.appendChild(fill);
    wrap.appendChild(bar);
    var line = 'Question ' + Math.min(session.index + 1, session.ids.length) + ' of ' + session.ids.length;
    line += ' · ' + modeLabel(session);
    line += ' · ' + sc.answered + ' answered';
    if (sc.answered) line += ' · Score ' + sc.correct + ' / ' + sc.answered + ' (' + percent(sc.correct, sc.answered) + '%)';
    wrap.appendChild(el('p', 'pt-status', line));
    return wrap;
  }

  function inputFor(question, part, value, disabled, name) {
    var long = (part && part.answer && part.answer.length > 42) ||
      (question.layout && (question.layout.blank === 'long' || question.layout.table === 'kata')) ||
      (question.type === 'short' && question.answer && question.answer.length > 42);
    var field = document.createElement(long ? 'textarea' : 'input');
    field.className = 'pt-input';
    if (!long) field.type = 'text';
    else field.rows = 2;
    field.value = value || '';
    field.disabled = !!disabled;
    field.autocomplete = 'off';
    field.autocapitalize = 'off';
    field.spellcheck = false;
    field.setAttribute('aria-label', name || 'Your answer');
    if (long) field.setAttribute('enterkeyhint', 'done');
    return field;
  }

  function markField(field, part) {
    if (!part) return;
    field.classList.add(part.correct ? 'ok' : 'bad');
    field.disabled = true;
  }

  function renderBlanks(question, result) {
    var grid = el('div', 'pt-grid');
    var cols = (question.layout && question.layout.per_row) || 1;
    grid.style.gridTemplateColumns = 'repeat(' + cols + ', minmax(0, 1fr))';
    if (cols >= 3 && question.layout && (question.layout.blank === 'num' || question.layout.blank === 'short')) {
      grid.classList.add('pt-compact');
    }
    question.parts.forEach(function (part, i) {
      var given = result && result.parts[i] ? result.parts[i].given : '';
      var fieldWrap = el('div', 'pt-field');
      var lab = el('label', '', part.label);
      var inputId = 'pt-blank-' + i;
      lab.htmlFor = inputId;
      if (hasKanji(part.label) || (question.layout && question.layout.kanji)) {
        lab.classList.add('pt-kanji');
        lab.lang = 'ja';
      }
      var field = inputFor(question, part, given, !!result, part.label);
      field.id = inputId;
      if (result) markField(field, result.parts[i]);
      fieldWrap.appendChild(lab);
      fieldWrap.appendChild(field);
      grid.appendChild(fieldWrap);
    });
    return grid;
  }

  function renderMatch(question, result) {
    var box = el('div', 'pt-match');
    var headers = question.header || ['Term', 'Answer'];
    var head = el('div', 'pt-match-head');
    head.appendChild(el('span', '', headers[0] || 'Term'));
    head.appendChild(el('span', '', headers[1] || 'Answer'));
    box.appendChild(head);
    question.pairs.forEach(function (pair, i) {
      var row = el('div', 'pt-match-row');
      var lab = el('label', '', pair.label + ' ' + pair.left);
      var selectId = 'pt-match-' + i;
      lab.htmlFor = selectId;
      var sel = el('select');
      sel.id = selectId;
      sel.setAttribute('aria-label', pair.left);
      var placeholder = el('option', '', 'Choose');
      placeholder.value = '';
      sel.appendChild(placeholder);
      (question.options || []).forEach(function (opt) {
        var letter = G.letterOf(opt);
        var option = el('option', '', opt);
        option.value = letter || opt;
        sel.appendChild(option);
      });
      if (result && result.parts[i]) {
        sel.value = G.letterOf(result.parts[i].given) || result.parts[i].given || '';
        sel.disabled = true;
        sel.classList.add(result.parts[i].correct ? 'ok' : 'bad');
      }
      row.appendChild(lab);
      row.appendChild(sel);
      box.appendChild(row);
    });
    return box;
  }

  function renderChoices(question, result) {
    var group = el('div', 'pt-options');
    group.setAttribute('role', 'group');
    group.setAttribute('aria-label', 'Choices');
    var picked = result && result.parts[0] ? result.parts[0].given : '';
    question.options.forEach(function (opt) {
      var b = el('button', 'pt-option', opt);
      b.type = 'button';
      b.setAttribute('data-act', 'pick');
      b.setAttribute('data-value', opt);
      b.setAttribute('aria-pressed', 'false');
      if (result) {
        b.disabled = true;
        if (G.normalize(opt) === G.normalize(question.answer)) b.classList.add('pt-key');
        else if (picked && G.normalize(opt) === G.normalize(picked)) b.classList.add('pt-no');
      }
      group.appendChild(b);
    });
    return group;
  }

  function feedbackBlock(question, result) {
    var box = el('div', 'pt-feedback ' + (result.correct ? 'ok' : 'bad'));
    box.setAttribute('aria-live', 'polite');
    var single = result.parts.length === 1;
    var part = result.parts[0];
    if (single && part.correct && part.close) {
      box.appendChild(el('p', 'pt-verdict', 'Correct — exact spelling: ' + part.expected));
    } else if (result.correct) {
      box.appendChild(el('p', 'pt-verdict', 'Correct'));
    } else if (single) {
      box.appendChild(el('p', 'pt-verdict', 'Incorrect'));
    } else {
      var n = result.parts.filter(function (p) { return p.correct; }).length;
      box.appendChild(el('p', 'pt-verdict', 'Incorrect — ' + n + ' of ' + result.parts.length + ' correct'));
    }
    if (!single) {
      var list = el('ul', 'pt-part-list');
      var labels = question.type === 'match'
        ? question.pairs.map(function (p) { return p.left; })
        : question.parts.map(function (p) { return p.label; });
      result.parts.forEach(function (p, i) {
        var text;
        if (p.correct && p.close) text = labels[i] + ': Correct — exact spelling: ' + p.expected;
        else if (p.correct) text = labels[i] + ': Correct';
        else if (p.expected) text = labels[i] + ': Incorrect — answer: ' + p.expected;
        else text = labels[i] + ': Incorrect';
        list.appendChild(el('li', p.correct ? 'pt-ok' : 'pt-bad', text));
      });
      box.appendChild(list);
    }
    box.appendChild(el('p', '', 'Answer: ' + result.answer));
    var pages = formatPages(result.page);
    if (pages) box.appendChild(el('p', 'muted', pages));
    if (result.note) box.appendChild(el('p', 'muted', result.note));
    return box;
  }

  function renderQuestion() {
    var session = state.session;
    var question = questionsById(session.ids[session.index]);
    if (!question) {
      session.phase = 'results';
      save();
      renderResults();
      return;
    }
    var result = session.phase === 'feedback' ? resultFor(session, question.id) : null;
    clear(app);
    app.appendChild(progressBlock(session));
    app.appendChild(el('p', 'pt-section', question.section));
    app.appendChild(el('h3', 'pt-q', question.prompt));
    if (!result && /any order/i.test(question.note || '')) {
      app.appendChild(el('p', 'muted', 'Any order.'));
    }
    if (question.type === 'fill') app.appendChild(renderBlanks(question, result));
    else if (question.type === 'match') app.appendChild(renderMatch(question, result));
    else if (question.type === 'mc') app.appendChild(renderChoices(question, result));
    else {
      var given = result && result.parts[0] ? result.parts[0].given : '';
      var field = inputFor(question, null, given, !!result, 'Your answer');
      field.id = 'pt-blank-0';
      if (result) markField(field, result.parts[0]);
      app.appendChild(field);
    }
    if (result) app.appendChild(feedbackBlock(question, result));
    var actions = el('div', 'pt-actions');
    if (!result) actions.appendChild(button('Check answer', 'check'));
    else if (session.index + 1 >= session.ids.length) actions.appendChild(button('See results', 'finish'));
    else actions.appendChild(button('Next', 'next'));
    actions.appendChild(button('Back', 'menu', 'g'));
    app.appendChild(actions);
  }

  function formatGiven(question, result) {
    if (question.type === 'fill') {
      return question.parts.map(function (part, i) {
        var given = result.parts[i] ? result.parts[i].given : '';
        return part.label + ': ' + (given.trim() ? given.trim() : '(blank)');
      }).join('\n');
    }
    if (question.type === 'match') {
      return question.pairs.map(function (pair, i) {
        var given = result.parts[i] ? result.parts[i].given : '';
        var letter = G.letterOf(given);
        var opt = (question.options || []).filter(function (item) { return G.letterOf(item) === letter; })[0];
        var shown = opt || given || '(blank)';
        return pair.left + ': ' + shown;
      }).join('\n');
    }
    var text = result.parts[0] ? result.parts[0].given : '';
    return text.trim() ? text.trim() : '(blank)';
  }

  function renderResults() {
    var session = state.session;
    clear(app);
    if (!session) {
      renderMenu();
      return;
    }
    var sc = scoreOf(session);
    var perfect = sc.total > 0 && sc.correct === sc.total;
    app.appendChild(el('h3', 'pt-q', 'Results'));
    app.appendChild(el('p', 'muted', modeLabel(session)));
    var score = el('p', 'pt-score ' + (perfect ? 'ok' : 'bad'), 'Score ' + sc.correct + ' / ' + sc.total + ' (' + percent(sc.correct, sc.total) + '%)');
    app.appendChild(score);
    app.appendChild(el('p', '', perfect ? '100% — a passing score on the written test.' : 'The written test needs 100%.'));

    var misses = session.ids.filter(function (id) {
      var result = resultFor(session, id);
      return result && !result.correct;
    });
    app.appendChild(el('h3', '', misses.length ? 'Missed questions' : 'No misses'));
    if (!misses.length) {
      app.appendChild(el('p', 'muted', 'Every question in this test was correct.'));
    }
    misses.forEach(function (id) {
      var question = questionsById(id);
      var result = resultFor(session, id);
      if (!question || !result) return;
      var card = el('article', 'pt-miss');
      card.appendChild(el('p', 'pt-section', question.section));
      card.appendChild(el('p', '', question.prompt));
      var yours = el('p', 'pt-pre', 'Your answer: ' + formatGiven(question, result));
      card.appendChild(yours);
      var ans = el('p', '');
      ans.appendChild(el('span', '', 'Answer: '));
      ans.appendChild(document.createTextNode(result.answer));
      card.appendChild(ans);
      var pages = formatPages(result.page);
      if (pages) card.appendChild(el('p', 'muted', pages));
      app.appendChild(card);
    });

    var actions = el('div', 'pt-actions');
    if (misses.length) actions.appendChild(button('Retry missed only (' + misses.length + ')', 'retry-session'));
    actions.appendChild(button('Try this set again', 'again', 'g'));
    actions.appendChild(button('Back', 'menu', 'g'));
    app.appendChild(actions);
    if (state.missed.length && state.missed.length !== misses.length) {
      app.appendChild(el('p', 'muted', 'Saved missed list: ' + state.missed.length + '. Retry missed only on the start screen uses that full list.'));
    }
  }

  function rememberMiss(id, correct) {
    var set = {};
    state.missed.forEach(function (item) { set[item] = true; });
    if (correct) delete set[id];
    else set[id] = true;
    state.missed = bank.map(function (q) { return q.id; }).filter(function (item) { return set[item]; });
  }

  function start(mode, ids, section) {
    confirmReset = false;
    state.session = {
      mode: mode,
      section: section || null,
      ids: ids,
      index: 0,
      phase: 'answer',
      results: {}
    };
    save();
    renderQuestion();
    focusStart();
  }

  function collectResponse(question) {
    if (question.type === 'mc') {
      var picked = app.querySelector('.pt-option[aria-pressed="true"]');
      return picked ? picked.getAttribute('data-value') : '';
    }
    if (question.type === 'match') {
      return question.pairs.map(function (_, i) {
        var sel = document.getElementById('pt-match-' + i);
        return sel ? sel.value : '';
      });
    }
    if (question.type === 'fill') {
      return question.parts.map(function (_, i) {
        var field = document.getElementById('pt-blank-' + i);
        return field ? field.value : '';
      });
    }
    var one = document.getElementById('pt-blank-0');
    return one ? one.value : '';
  }

  function check() {
    var session = state.session;
    if (!session || session.phase !== 'answer') return;
    var question = questionsById(session.ids[session.index]);
    if (!question) return;
    var response = collectResponse(question);
    var graded = G.gradeQuestion(question, response);
    session.results[question.id] = graded;
    session.phase = 'feedback';
    rememberMiss(question.id, graded.correct);
    save();
    renderQuestion();
  }

  function next() {
    var session = state.session;
    if (!session) return;
    session.index += 1;
    if (session.index >= session.ids.length) {
      session.phase = 'results';
      save();
      renderResults();
      focusStart();
      return;
    }
    session.phase = 'answer';
    save();
    renderQuestion();
    focusStart();
  }

  function focusStart() {
    var target = document.getElementById('practice');
    if (target && target.scrollIntoView) target.scrollIntoView({ block: 'start' });
    var field = app.querySelector('input, textarea, select, button');
    if (field && field.focus) field.focus();
  }

  function onClick(event) {
    var pick = event.target.closest('[data-act="pick"]');
    if (pick && app.contains(pick) && !pick.disabled) {
      app.querySelectorAll('.pt-option').forEach(function (btn) {
        btn.setAttribute('aria-pressed', btn === pick ? 'true' : 'false');
      });
      return;
    }
    var node = event.target.closest('[data-act]');
    if (!node || !app.contains(node) || node.disabled) return;
    var act = node.getAttribute('data-act');
    if (act === 'order') start('order', bank.map(function (q) { return q.id; }));
    else if (act === 'shuffle') start('shuffle', shuffle(bank.map(function (q) { return q.id; })));
    else if (act === 'section') {
      var sel = document.getElementById('pt-section');
      var name = sel ? sel.value : sections()[0];
      var ids = bank.filter(function (q) { return q.section === name; }).map(function (q) { return q.id; });
      start('section', ids, name);
    } else if (act === 'missed') {
      if (!state.missed.length) return;
      start('missed', state.missed.slice());
    } else if (act === 'retry-session') {
      var session = state.session;
      if (!session) return;
      var ids = session.ids.filter(function (id) {
        var result = resultFor(session, id);
        return result && !result.correct;
      });
      if (!ids.length) return;
      start('missed', ids);
    } else if (act === 'again') {
      var again = state.session;
      if (!again) return renderMenu();
      var set = again.ids.slice().sort(function (a, b) { return a - b; });
      if (again.mode === 'shuffle') set = shuffle(set);
      start(again.mode, set, again.section);
    } else if (act === 'check') check();
    else if (act === 'next' || act === 'finish') next();
    else if (act === 'continue') {
      confirmReset = false;
      if (state.session && state.session.phase === 'results') renderResults();
      else renderQuestion();
    } else if (act === 'results') renderResults();
    else if (act === 'menu') {
      confirmReset = false;
      renderMenu();
    } else if (act === 'reset-ask') {
      confirmReset = true;
      renderMenu();
    } else if (act === 'reset-no') {
      confirmReset = false;
      renderMenu();
    } else if (act === 'reset-do') {
      confirmReset = false;
      state = { missed: [], session: null };
      try { localStorage.removeItem(KEY); } catch (e) {}
      renderMenu();
      app.insertBefore(el('p', 'okmsg', 'Progress cleared.'), app.firstChild);
    }
  }

  function onKey(event) {
    if (event.key !== 'Enter') return;
    if (!event.target.matches || !event.target.matches('input.pt-input')) return;
    if (!state.session || state.session.phase !== 'answer') return;
    var inputs = Array.prototype.slice.call(app.querySelectorAll('input.pt-input'));
    var idx = inputs.indexOf(event.target);
    if (idx >= 0 && idx < inputs.length - 1) {
      event.preventDefault();
      inputs[idx + 1].focus();
      return;
    }
    event.preventDefault();
    check();
  }

  function boot(data) {
    bank = (data && data.questions) || [];
    if (!G) {
      clear(app);
      app.appendChild(el('p', '', 'The practice test could not start.'));
      return;
    }
    load();
    app.addEventListener('click', onClick);
    app.addEventListener('keydown', onKey);
    if (state.session && state.session.phase === 'results') renderResults();
    else if (state.session && state.session.phase === 'feedback') renderQuestion();
    else if (state.session && state.session.phase === 'answer') renderQuestion();
    else renderMenu();
  }

  fetch('data/practice-test.json')
    .then(function (res) {
      if (!res.ok) throw new Error('load');
      return res.json();
    })
    .then(boot)
    .catch(function () {
      clear(app);
      app.appendChild(el('p', '', 'The practice test questions could not be loaded. Refresh the page.'));
    });
})();
