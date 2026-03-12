const API_BASE = process.env.API_BASE || "http://localhost:8000";

const contactsListEl = document.getElementById("contacts-list");
const addContactBtn = document.getElementById("add-contact-btn");
const firstNameInput = document.getElementById("first-name");
const lastNameInput = document.getElementById("last-name");
const emailsListEl = document.getElementById("emails-list");
const addEmailBtn = document.getElementById("add-email-btn");
const saveContactBtn = document.getElementById("save-contact-btn");
const deleteContactBtn = document.getElementById("delete-contact-btn");
const emailErrorId = "email-error-message";
const deleteSelectedBtn = document.getElementById("delete-selected-btn");
const searchInput = document.getElementById("search-input");
const statusMessageEl = document.getElementById("status-message");
const welcomePanelEl = document.getElementById("welcome-panel");
const welcomeDismissBtn = document.getElementById("welcome-dismiss-btn");

let contacts = [];
let selectedContactId = null;
let multiSelectedIds = new Set();
let selectionAnchorId = null;
let currentSearchQuery = "";

async function fetchContacts(query = "") {
  const url = query
    ? `${API_BASE}/contacts?q=${encodeURIComponent(query)}`
    : `${API_BASE}/contacts`;
  const res = await fetch(url);
  contacts = await res.json();
  renderContactsList();
  if (contacts.length === 0 && query) {
    clearForm();
    return;
  }
  if (selectedContactId) {
    const stillExists = contacts.find((c) => c.id === selectedContactId);
    if (!stillExists) {
      clearForm();
    }
  }
}

function selectAllContacts() {
  multiSelectedIds = new Set(contacts.map((c) => c.id));
  renderContactsList();
}

function clearAllSelections() {
  if (multiSelectedIds.size === 0) return;
  multiSelectedIds.clear();
  renderContactsList();
}

function showStatusMessage(message, type = "success", timeoutMs = 2000) {
  if (!statusMessageEl) return;
  statusMessageEl.textContent = message;
  statusMessageEl.classList.remove("hidden", "success");
  if (type) {
    statusMessageEl.classList.add(type);
  }
  if (timeoutMs > 0) {
    setTimeout(() => {
      statusMessageEl.classList.add("hidden");
    }, timeoutMs);
  }
}

function moveSelection(delta, withShift = false) {
  if (!contacts.length) return;

  let index = contacts.findIndex((c) => c.id === selectedContactId);
  if (index === -1) {
    index = delta > 0 ? 0 : contacts.length - 1;
  } else {
    index += delta;
    if (index < 0) index = 0;
    if (index >= contacts.length) index = contacts.length - 1;
  }

  const next = contacts[index];
  if (!next) return;

  if (withShift) {
    if (!selectionAnchorId || !contacts.some((c) => c.id === selectionAnchorId)) {
      selectionAnchorId = selectedContactId || next.id;
    }
    const anchorIndex = contacts.findIndex((c) => c.id === selectionAnchorId);
    const start = Math.min(anchorIndex, index);
    const end = Math.max(anchorIndex, index);
    multiSelectedIds = new Set();
    for (let i = start; i <= end; i++) {
      multiSelectedIds.add(contacts[i].id);
    }
  }

  selectContact(next.id, !withShift);

  const itemEl = contactsListEl.querySelector(`li[data-id="${next.id}"]`);
  if (itemEl && typeof itemEl.scrollIntoView === "function") {
    itemEl.scrollIntoView({ block: "nearest" });
  }
}

function renderContactsList() {
  contactsListEl.innerHTML = "";
  const showMultiSelectUI = multiSelectedIds.size > 1;
  contacts.forEach((contact) => {
    const li = document.createElement("li");
    li.className = "contact-item" + (contact.id === selectedContactId ? " active" : "");
    li.dataset.id = contact.id;

    if (showMultiSelectUI) {
      const checkbox = document.createElement("input");
      checkbox.type = "checkbox";
      checkbox.className = "contact-select-checkbox";
      checkbox.checked = multiSelectedIds.has(contact.id);
      checkbox.addEventListener("click", (event) => {
        event.stopPropagation();
      });
      checkbox.addEventListener("change", (event) => {
        if (event.target.checked) {
          multiSelectedIds.add(contact.id);
        } else {
          multiSelectedIds.delete(contact.id);
        }
        renderContactsList();
      });
      li.appendChild(checkbox);
    }

    const span = document.createElement("span");
    span.className = "contact-item-name";
    span.textContent = `${contact.first_name} ${contact.last_name}`;

    li.appendChild(span);
    li.addEventListener("click", (event) => {
      if (event.shiftKey) {
        if (!selectionAnchorId || !contacts.some((c) => c.id === selectionAnchorId)) {
          selectionAnchorId = selectedContactId || contact.id;
        }
        const anchorIndex = contacts.findIndex((c) => c.id === selectionAnchorId);
        const targetIndex = contacts.findIndex((c) => c.id === contact.id);
        if (anchorIndex !== -1 && targetIndex !== -1) {
          const start = Math.min(anchorIndex, targetIndex);
          const end = Math.max(anchorIndex, targetIndex);
          multiSelectedIds = new Set();
          for (let i = start; i <= end; i++) {
            multiSelectedIds.add(contacts[i].id);
          }
        }
        selectContact(contact.id, false);
        renderContactsList();
      } else {
        selectContact(contact.id);
      }
    });
    contactsListEl.appendChild(li);
  });

  if (deleteSelectedBtn) {
    if (multiSelectedIds.size > 1) {
      deleteSelectedBtn.classList.remove("hidden");
    } else {
      deleteSelectedBtn.classList.add("hidden");
    }
  }
}

async function selectContact(id, updateAnchor = true) {
  selectedContactId = id;
  if (updateAnchor) {
    selectionAnchorId = id;
  }
  const res = await fetch(`${API_BASE}/contacts/${id}`);
  if (!res.ok) {
    return;
  }
  const contact = await res.json();
  populateForm(contact);
  renderContactsList();
}

function populateForm(contact) {
  firstNameInput.value = contact.first_name;
  lastNameInput.value = contact.last_name;
  renderEmails(contact.emails || []);
  deleteContactBtn.classList.remove("hidden");
}

function clearForm() {
  selectedContactId = null;
  selectionAnchorId = null;
  multiSelectedIds.clear();
  firstNameInput.value = "";
  lastNameInput.value = "";
  renderEmails([]);
  deleteContactBtn.classList.add("hidden");
  renderContactsList();
}

function renderEmails(emails) {
  emailsListEl.innerHTML = "";
  if (!emails || emails.length === 0) {
    emailsListEl.classList.add("hidden");
    return;
  }
  emailsListEl.classList.remove("hidden");
  emails.forEach((email) => addEmailRow(email));
}

function addEmailRow(value = "") {
  const li = document.createElement("li");
  li.className = "email-item";

  const input = document.createElement("input");
  input.type = "email";
  input.value = value;

  const removeBtn = document.createElement("button");
  removeBtn.className = "email-remove-btn";
  removeBtn.textContent = "Delete";
  removeBtn.addEventListener("click", () => {
    emailsListEl.removeChild(li);
    if (emailsListEl.children.length === 0) {
      emailsListEl.classList.add("hidden");
    }
  });

  li.appendChild(input);
  li.appendChild(removeBtn);
  emailsListEl.appendChild(li);
  emailsListEl.classList.remove("hidden");
}

function getEmailsFromForm() {
  const inputs = emailsListEl.querySelectorAll("input[type='email']");
  const emails = [];
  inputs.forEach((input) => {
    const v = input.value.trim();
    if (v) {
      emails.push(v);
    }
  });
  return emails;
}

function validateEmails(emails) {
  if (!emails.length) {
    return { ok: true, message: "" };
  }

  const simplePattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  const invalid = emails.find((e) => !simplePattern.test(e));

  if (invalid) {
    return { ok: false, message: `Invalid email: ${invalid}` };
  }

  return { ok: true, message: "" };
}

function showEmailError(message) {
  let errorEl = document.getElementById(emailErrorId);
  if (!errorEl) {
    errorEl = document.createElement("div");
    errorEl.id = emailErrorId;
    errorEl.className = "field-error";
    emailsListEl.parentElement.appendChild(errorEl);
  }
  errorEl.textContent = message;
}

function clearEmailError() {
  const errorEl = document.getElementById(emailErrorId);
  if (errorEl) {
    errorEl.textContent = "";
  }
}

async function saveContact() {
  const first_name = firstNameInput.value.trim();
  const last_name = lastNameInput.value.trim();
  const emails = getEmailsFromForm();

  if (!first_name || !last_name) {
    alert("First and last name are required.");
    return;
  }

  const emailValidation = validateEmails(emails);
  if (!emailValidation.ok) {
    showEmailError(emailValidation.message);
    return;
  }
  clearEmailError();

  const payload = { first_name, last_name, emails };

  let res;
  if (selectedContactId) {
    res = await fetch(`${API_BASE}/contacts/${selectedContactId}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
  } else {
    res = await fetch(`${API_BASE}/contacts`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
  }

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    alert("Error saving contact: " + (err.detail || res.statusText));
    return;
  }

  const saved = await res.json();
  selectedContactId = saved.id;
  populateForm(saved);
  await fetchContacts(currentSearchQuery);
  showStatusMessage("Contact saved successfully.", "success");
}

async function deleteSelectedContacts() {
  if (multiSelectedIds.size === 0) {
    alert("No contacts selected.");
    return;
  }

  const count = multiSelectedIds.size;
  const confirmDelete = confirm(`Delete ${count} selected contact(s)?`);
  if (!confirmDelete) return;

  const idsToDelete = Array.from(multiSelectedIds);

  for (const id of idsToDelete) {
    try {
      const res = await fetch(`${API_BASE}/contacts/${id}`, {
        method: "DELETE",
      });
      if (!res.ok && res.status !== 204) {
        console.error("Failed to delete contact", id, res.status);
      }
    } catch (e) {
      console.error("Error deleting contact", id, e);
    }
  }

  if (selectedContactId && multiSelectedIds.has(selectedContactId)) {
    clearForm();
  }

  multiSelectedIds.clear();
  await fetchContacts(currentSearchQuery);
}

async function deleteContact() {
  if (!selectedContactId) return;
  const confirmDelete = confirm("Delete this contact?");
  if (!confirmDelete) return;

  const res = await fetch(`${API_BASE}/contacts/${selectedContactId}`, {
    method: "DELETE",
  });

  if (!res.ok && res.status !== 204) {
    alert("Error deleting contact");
    return;
  }

  clearForm();
  await fetchContacts(currentSearchQuery);
}

addContactBtn.addEventListener("click", () => {
  clearForm();
});

addEmailBtn.addEventListener("click", () => {
  addEmailRow("");
});

saveContactBtn.addEventListener("click", () => {
  saveContact().catch((e) => console.error(e));
});

deleteContactBtn.addEventListener("click", () => {
  deleteContact().catch((e) => console.error(e));
});

deleteSelectedBtn.addEventListener("click", () => {
  deleteSelectedContacts().catch((e) => console.error(e));
});

let searchDebounceId = null;
searchInput.addEventListener("input", (event) => {
  const value = event.target.value.trim();
  currentSearchQuery = value;
  if (searchDebounceId) {
    clearTimeout(searchDebounceId);
  }
  searchDebounceId = setTimeout(() => {
    fetchContacts(currentSearchQuery).catch((e) => console.error(e));
  }, 300);
});

document.addEventListener("keydown", (event) => {
  const tag = event.target.tagName;
  if (tag === "INPUT" || tag === "TEXTAREA") {
    return;
  }

  if (event.ctrlKey && (event.key === "a" || event.key === "A")) {
    event.preventDefault();
    selectAllContacts();
    return;
  }

  if (event.key === "ArrowDown") {
    event.preventDefault();
    moveSelection(1, event.shiftKey);
    return;
  }

  if (event.key === "ArrowUp") {
    event.preventDefault();
    moveSelection(-1, event.shiftKey);
    return;
  }

  if (event.key === "Escape") {
    event.preventDefault();
    clearAllSelections();
    return;
  }
});

// Initial state
clearForm();
fetchContacts(currentSearchQuery).catch((e) => console.error(e));

const WELCOME_STORAGE_KEY = "contacts_has_seen_welcome";
if (welcomePanelEl && welcomeDismissBtn) {
  const hasSeen = window.localStorage.getItem(WELCOME_STORAGE_KEY) === "true";
  if (!hasSeen) {
    welcomePanelEl.classList.remove("hidden");
  }
  welcomeDismissBtn.addEventListener("click", () => {
    window.localStorage.setItem(WELCOME_STORAGE_KEY, "true");
    welcomePanelEl.classList.add("hidden");
  });
}

