# FormApp cookbook

Snippets for `Code.gs`. The entry function must `return` an object (Apps Script API `scripts.run` only accepts JSON-serializable return values — do not return the `Form` or item objects themselves).

## Skeleton

```javascript
function buildForm() {
  var form = FormApp.create('제목')
    .setDescription('설명')
    .setCollectEmail(false)          // true asks respondents to submit their email
    .setLimitOneResponsePerUser(false)
    .setConfirmationMessage('제출해 주셔서 감사합니다.');

  // ... add items here ...

  return {
    formId: form.getId(),
    editUrl: form.getEditUrl(),
    publishedUrl: form.getPublishedUrl()
  };
}
```

## Question types

```javascript
// Short text
form.addTextItem().setTitle('이름').setRequired(true);

// Paragraph text
form.addParagraphTextItem().setTitle('자세한 의견을 남겨주세요');

// Multiple choice (single select)
form.addMultipleChoiceItem()
  .setTitle('만족도')
  .setChoiceValues(['매우 좋음', '좋음', '보통', '나쁨'])
  .setRequired(true);

// Checkboxes (multi select)
form.addCheckboxItem()
  .setTitle('관심 분야 (복수 선택 가능)')
  .setChoiceValues(['기획', '디자인', '개발', '마케팅']);

// Dropdown
form.addListItem().setTitle('부서').setChoiceValues(['영업', '개발', '인사']);

// Linear scale (e.g. 1-5 satisfaction)
form.addScaleItem()
  .setTitle('전반적으로 만족하셨나요?')
  .setBounds(1, 5)
  .setLabels('전혀 아니다', '매우 그렇다');

// Grid (rows x same choices per row)
form.addGridItem()
  .setTitle('항목별 평가')
  .setRows(['품질', '속도', '가격'])
  .setColumns(['나쁨', '보통', '좋음']);

// Checkbox grid
form.addCheckboxGridItem()
  .setTitle('해당하는 항목을 모두 선택하세요')
  .setRows(['월', '화', '수'])
  .setColumns(['오전', '오후', '저녁']);

// Date / time
form.addDateItem().setTitle('희망 날짜');
form.addTimeItem().setTitle('희망 시간');

// File upload (requires the form owner's Drive; response files land in a Drive folder)
form.addFileUploadItem().setTitle('첨부파일');

// Section break (visually groups items after it)
form.addSectionHeaderItem().setTitle('2부: 추가 질문');

// Page break (multi-page form; label is the button text to reach this page)
form.addPageBreakItem().setTitle('다음 페이지');
```

## Validation

```javascript
var item = form.addTextItem().setTitle('이메일');
item.setValidation(
  FormApp.createTextValidation()
    .setHelpText('올바른 이메일 형식으로 입력하세요.')
    .requireTextIsEmail()
    .build()
);
```

Other builders: `requireTextIsUrl()`, `requireTextMatchesPattern(regex)`, `requireNumberBetween(min, max)` (on `createTextValidation` for number-only fields), etc.

## Quiz mode with grading

```javascript
form.setIsQuiz(true);

var mc = form.addMultipleChoiceItem().setTitle('1 + 1 = ?');
mc.setChoices([
  mc.createChoice('1', false),
  mc.createChoice('2', true),   // correct answer
  mc.createChoice('3', false)
]);
mc.setPoints(10);
mc.setFeedbackForCorrect(FormApp.createFeedback().setText('정답입니다!').build());
mc.setFeedbackForIncorrect(FormApp.createFeedback().setText('다시 확인해보세요.').build());
```

## Closing a form to new responses

FormApp has no "close on date X" setting — Forms just accepts responses until told to stop. Two options:
- Close immediately at creation time (rare): `form.setAcceptingResponses(false)`.
- Close automatically at a future date: this needs a **separate time-based Apps Script trigger** on the runner project (`ScriptApp.newTrigger(...).timeBased()...`), which is out of scope for a one-shot `scripts.run` call. If the user needs a scheduled close, tell them to close it manually in Google Forms on the target date, or flag this as a limitation rather than fabricating an unsupported feature.

## Common mistakes

- `addCheckboxItem()`/`addMultipleChoiceItem()` return the item itself from `.setChoiceValues(...)`, so you can chain `.setRequired(true)` after — but `.setChoices([...])` (used for quiz grading) takes an array of `Choice` objects built via `item.createChoice(...)`, not plain strings. Mixing the two up is the most common bug.
- Every builder call must end the chain with something JSON-serializable in the `return` — an accidental `return form;` breaks `scripts.run` (it can't serialize a `Form` object).
