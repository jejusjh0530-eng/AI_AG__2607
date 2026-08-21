/**
 * Generic Google Form builder, driven entirely by the JSON object passed
 * as `spec` when this function is invoked via the Apps Script Execution
 * API (script.scripts.run). One persistent script project runs this same
 * function for every form the gws-forms skill builds -- only `spec`
 * changes between calls.
 *
 * spec = {
 *   title: string,
 *   description?: string,
 *   isQuiz?: boolean,
 *   collectEmail?: boolean,
 *   limitOneResponsePerUser?: boolean,
 *   confirmationMessage?: string,
 *   items: [
 *     { type: "text"|"paragraph", title, helpText?, required? },
 *     { type: "multiple_choice"|"checkbox"|"dropdown", title, choices: string[], helpText?, required?,
 *       correctAnswers?: string[], points?: number },
 *     { type: "scale", title, lower?: number, upper?: number, lowerLabel?: string, upperLabel?: string, required? },
 *     { type: "date", title, includeYear?: boolean, required? },
 *     { type: "time", title, required? },
 *     { type: "section", title, helpText? }
 *   ]
 * }
 *
 * Returns { formId, editUrl, publishedUrl }.
 */
function createForm(spec) {
  var form = FormApp.create(spec.title);
  if (spec.description) form.setDescription(spec.description);
  if (spec.isQuiz) form.setIsQuiz(true);
  if (spec.collectEmail) form.setCollectEmail(true);
  if (spec.limitOneResponsePerUser) form.setLimitOneResponsePerUser(true);
  if (spec.confirmationMessage) form.setConfirmationMessage(spec.confirmationMessage);

  (spec.items || []).forEach(function (item) {
    var q;
    switch (item.type) {
      case 'text':
        q = form.addTextItem();
        break;
      case 'paragraph':
        q = form.addParagraphTextItem();
        break;
      case 'multiple_choice':
        q = form.addMultipleChoiceItem();
        applyChoices(q, item, spec.isQuiz);
        break;
      case 'checkbox':
        q = form.addCheckboxItem();
        applyChoices(q, item, spec.isQuiz);
        break;
      case 'dropdown':
        q = form.addListItem();
        applyChoices(q, item, spec.isQuiz);
        break;
      case 'scale':
        q = form.addScaleItem();
        q.setBounds(item.lower != null ? item.lower : 1, item.upper != null ? item.upper : 5);
        if (item.lowerLabel || item.upperLabel) {
          q.setLabels(item.lowerLabel || '', item.upperLabel || '');
        }
        break;
      case 'date':
        q = form.addDateItem();
        if (item.includeYear != null) q.setIncludesYear(item.includeYear);
        break;
      case 'time':
        q = form.addTimeItem();
        break;
      case 'section':
        q = form.addPageBreakItem();
        break;
      default:
        throw new Error('Unknown item type: ' + item.type);
    }
    q.setTitle(item.title);
    if (item.helpText && q.setHelpText) q.setHelpText(item.helpText);
    if (item.required && q.setRequired) q.setRequired(true);
  });

  return {
    formId: form.getId(),
    editUrl: form.getEditUrl(),
    publishedUrl: form.getPublishedUrl(),
  };
}

function applyChoices(item, spec, isQuiz) {
  var choices = spec.choices || [];
  if (isQuiz && spec.correctAnswers && spec.correctAnswers.length) {
    var built = choices.map(function (text) {
      var correct = spec.correctAnswers.indexOf(text) !== -1;
      return item.createChoice(text, correct);
    });
    item.setChoices(built);
    if (spec.points != null) item.setPoints(spec.points);
  } else {
    item.setChoiceValues(choices);
  }
}
