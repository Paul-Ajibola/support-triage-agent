
/* =========================
   CONFIGURATION
========================= */

const API_BASE_URL =
  window.API_BASE_URL ||
  "http://localhost:8000";

const TRIAGE_ENDPOINT =
  `${API_BASE_URL}/triage`;


/* =========================
   DOM ELEMENTS
========================= */

const subjectInput =
  document.getElementById("ticketSubject");

const messageInput =
  document.getElementById("ticketMessage");

const characterCount =
  document.getElementById("characterCount");

const analyzeButton =
  document.getElementById("analyzeButton");

const analyzeText =
  document.getElementById("analyzeText");

const loadingSpinner =
  document.getElementById("loadingSpinner");

const clearButton =
  document.getElementById("clearButton");

const resultCard =
  document.getElementById("resultCard");

const errorCard =
  document.getElementById("errorCard");

const errorMessage =
  document.getElementById("errorMessage");

const categoryValue =
  document.getElementById("categoryValue");

const urgencyValue =
  document.getElementById("urgencyValue");

const modelValue =
  document.getElementById("modelValue");

const routingMessage =
  document.getElementById("routingMessage");

const rawResponse =
  document.getElementById("rawResponse");

const toggleRawResponse =
  document.getElementById("toggleRawResponse");

const recentTickets =
  document.getElementById("recentTickets");

const ticketsToday =
  document.getElementById("ticketsToday");

const criticalTickets =
  document.getElementById("criticalTickets");

const clearHistory =
  document.getElementById("clearHistory");

const modelStatus =
  document.getElementById("modelStatus");

const modelStatusDot =
  document.getElementById("modelStatusDot");


/* =========================
   LOCAL STATE
========================= */

let history =
  JSON.parse(
    localStorage.getItem("supportTriageHistory") || "[]"
  );


/* =========================
   EXAMPLE TICKETS
========================= */

const examples = {

  password: {
    subject: "Unable to reset my password",

    message:
      "I requested a password reset email several times but I haven't received anything. I need to access my account urgently."
  },

  billing: {
    subject: "I was charged twice",

    message:
      "I checked my bank statement and I can see two charges for the same subscription. Please help me understand what happened and refund the duplicate charge."
  },

  bug: {
    subject: "Dashboard keeps crashing",

    message:
      "Every time I try to open the analytics dashboard the application crashes. This started after the latest update and I cannot access my reports."
  }

};


/* =========================
   CHARACTER COUNT
========================= */

messageInput.addEventListener(
  "input",
  () => {

    const length =
      messageInput.value.length;

    characterCount.textContent =
      `${length} / 5000`;

  }
);


/* =========================
   EXAMPLE BUTTONS
========================= */

document
  .querySelectorAll(".example-button")
  .forEach(button => {

    button.addEventListener(
      "click",
      () => {

        const example =
          examples[button.dataset.example];

        if (!example) {
          return;
        }

        subjectInput.value =
          example.subject;

        messageInput.value =
          example.message;

        messageInput.dispatchEvent(
          new Event("input")
        );

        subjectInput.focus();

      }
    );

  });


/* =========================
   CLEAR
========================= */

clearButton.addEventListener(
  "click",
  clearForm
);


function clearForm() {

  subjectInput.value = "";

  messageInput.value = "";

  characterCount.textContent =
    "0 / 5000";

  resultCard.classList.add(
    "hidden"
  );

  errorCard.classList.add(
    "hidden"
  );

}


/* =========================
   ANALYZE
========================= */

analyzeButton.addEventListener(
  "click",
  analyzeTicket
);


async function analyzeTicket() {

  const subject =
    subjectInput.value.trim();

  const message =
    messageInput.value.trim();


  if (!message) {

    showError(
      "Please enter a customer support message before analyzing the ticket."
    );

    return;

  }


  setLoading(true);

  hideError();

  resultCard.classList.add(
    "hidden"
  );


  try {

    /*
     * The backend can accept either:
     *
     * {
     *   "subject": "...",
     *   "message": "..."
     * }
     *
     * or another Pydantic-compatible structure.
     *
     * Change this object if your backend schema differs.
     */

    const response =
      await fetch(
        TRIAGE_ENDPOINT,
        {
          method: "POST",

          headers: {
            "Content-Type":
              "application/json"
          },

          body: JSON.stringify({
            subject,
            message
          })
        }
      );


    if (!response.ok) {

      const text =
        await response.text();

      throw new Error(
        text ||
        `API returned HTTP ${response.status}`
      );

    }


    const data =
      await response.json();


    displayResult(
      data,
      subject,
      message
    );


    saveTicket(
      data,
      subject,
      message
    );


  } catch (error) {

    console.error(
      "Triage request failed:",
      error
    );

    showError(
      error.message ||
      "The triage service could not be reached."
    );

    modelStatus.textContent =
      "Unavailable";

    modelStatusDot.style.background =
      "#d64545";

  } finally {

    setLoading(false);

  }

}


/* =========================
   DISPLAY RESULT
========================= */

function displayResult(
  data,
  subject,
  message
) {

  /*
   * The backend may return:
   *
   * {
   *   category: "auth",
   *   urgency: "high"
   * }
   *
   * or:
   *
   * {
   *   result: {
   *     category: "...",
   *     urgency: "..."
   *   }
   * }
   *
   * The helper below handles both.
   */

  const result =
    data.result ||
    data;


  const category =
    result.category ||
    result.classification?.category ||
    "general";


  const urgency =
    result.urgency ||
    result.priority ||
    result.classification?.urgency ||
    "normal";


  const model =
    result.model ||
    result.model_name ||
    data.model ||
    "Support Triage AI";


  const fallback =
    result.fallback ||
    data.fallback ||
    false;


  categoryValue.textContent =
    formatCategory(category);


  urgencyValue.textContent =
    formatUrgency(urgency);


  modelValue.textContent =
    fallback
      ? "Fallback model"
      : model;


  routingMessage.textContent =
    buildRoutingMessage(
      category,
      urgency
    );


  rawResponse.textContent =
    JSON.stringify(
      data,
      null,
      2
    );


  resultCard.classList.remove(
    "hidden"
  );


  modelStatus.textContent =
    fallback
      ? "Fallback active"
      : "Ready";


  modelStatusDot.style.background =
    fallback
      ? "#c98316"
      : "#1f9d68";

}


/* =========================
   ROUTING
========================= */

function buildRoutingMessage(
  category,
  urgency
) {

  const teams = {

    auth:
      "Route to the authentication / account access team.",

    billing:
      "Route to the billing and payments team.",

    integration:
      "Route to the integrations team.",

    bug_report:
      "Route to the engineering / bug resolution team.",

    feature_request:
      "Route to the product team for feature review.",

    account_management:
      "Route to the account management team.",

    performance:
      "Route to the engineering / performance team.",

    general:
      "Route to the general support queue."

  };


  let message =
    teams[category] ||
    teams.general;


  if (
    urgency === "critical"
  ) {

    message +=
      " Mark this ticket for immediate attention.";

  } else if (
    urgency === "high"
  ) {

    message +=
      " Prioritize this ticket for expedited review.";

  }


  return message;

}


/* =========================
   FORMATTERS
========================= */

function formatCategory(
  category
) {

  return String(category)
    .replaceAll("_", " ")
    .replace(
      /\b\w/g,
      char =>
        char.toUpperCase()
    );

}


function formatUrgency(
  urgency
) {

  return String(urgency)
    .replaceAll("_", " ")
    .replace(
      /\b\w/g,
      char =>
        char.toUpperCase()
    );

}


/* =========================
   LOADING STATE
========================= */

function setLoading(
  loading
) {

  analyzeButton.disabled =
    loading;


  if (loading) {

    analyzeText.textContent =
      "Analyzing...";

    loadingSpinner.classList.remove(
      "hidden"
    );

  } else {

    analyzeText.textContent =
      "Analyze ticket";

    loadingSpinner.classList.add(
      "hidden"
    );

  }

}


/* =========================
   ERROR
========================= */

function showError(
  message
) {

  errorMessage.textContent =
    message;

  errorCard.classList.remove(
    "hidden"
  );

}


function hideError() {

  errorCard.classList.add(
    "hidden"
  );

}


/* =========================
   HISTORY
========================= */

function saveTicket(
  data,
  subject,
  message
) {

  const result =
    data.result ||
    data;


  const ticket = {

    id:
      Date.now(),

    subject:
      subject ||
      "Untitled ticket",

    message,

    category:
      result.category ||
      result.classification?.category ||
      "general",

    urgency:
      result.urgency ||
      result.priority ||
      result.classification?.urgency ||
      "normal",

    createdAt:
      new Date().toISOString()

  };


  history.unshift(
    ticket
  );


  history =
    history.slice(0, 10);


  localStorage.setItem(
    "supportTriageHistory",
    JSON.stringify(history)
  );


  renderHistory();

}


/* =========================
   RENDER HISTORY
========================= */

function renderHistory() {

  if (!history.length) {

    recentTickets.innerHTML = `
      <div class="empty-state">
        No tickets analyzed yet.
      </div>
    `;

    ticketsToday.textContent =
      "0";

    criticalTickets.textContent =
      "0";

    return;

  }


  recentTickets.innerHTML =
    history
      .map(ticket => {

        const urgency =
          String(
            ticket.urgency
          ).toLowerCase();


        return `
          <div class="recent-ticket">

            <div class="recent-subject">
              ${escapeHtml(
                ticket.subject
              )}
            </div>

            <div class="recent-meta">

              <span class="recent-category">
                ${escapeHtml(
                  formatCategory(
                    ticket.category
                  )
                )}
              </span>

              <span
                class="urgency-badge urgency-${escapeHtml(
                  urgency
                )}"
              >
                ${escapeHtml(
                  urgency
                )}
              </span>

            </div>

          </div>
        `;

      })
      .join("");


  ticketsToday.textContent =
    history.length;


  criticalTickets.textContent =
    history.filter(
      ticket =>
        String(
          ticket.urgency
        ).toLowerCase() ===
        "critical"
    ).length;

}


/* =========================
   CLEAR HISTORY
========================= */

clearHistory.addEventListener(
  "click",
  () => {

    history = [];

    localStorage.removeItem(
      "supportTriageHistory"
    );

    renderHistory();

  }
);


/* =========================
   RAW RESPONSE
========================= */

toggleRawResponse.addEventListener(
  "click",
  () => {

    rawResponse.classList.toggle(
      "hidden"
    );

  }
);


/* =========================
   HTML ESCAPING
========================= */

function escapeHtml(
  value
) {

  return String(value)

    .replaceAll(
      "&",
      "&amp;"
    )

    .replaceAll(
      "<",
      "&lt;"
    )

    .replaceAll(
      ">",
      "&gt;"
    )

    .replaceAll(
      '"',
      "&quot;"
    )

    .replaceAll(
      "'",
      "&#039;"
    );

}


/* =========================
   INITIALIZATION
========================= */

renderHistory();