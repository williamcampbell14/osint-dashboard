var toolsConfig = [
    {
        dataKey: "Cookies",
        dictionary: {},
        ignoredItems: []
    },
    {
        dataKey: "IP Info",
        dictionary: {
            "ip": "IP",
            "anycast": "Anycast network architecture",
            "org": "Organization",
            "postal": "ZIP Code",
            "country_name": "Country"
        },
        ignoredItems: ["isEU", "country_flag_url", "country", "country_flag", "country_currency", "continent", "loc"]
    },
    {
        dataKey: "Headers",
        dictionary: {
            "pragma": "Pragma (Catching) Info",
            "server": "Web Server Info"
        },
        ignoredItems: ["perf", "expiry", "set-cookie"]
    },
    {
        dataKey: "Domain",
        dictionary: {
            "A": "'A' (address) Record",
            "NS": "'NS' (nameserver) Record",
            "SOA": "'SOA' (start of authority) Record",
            "MX": "'MX' (mail exchange) Record"
        },
        ignoredItems: []
    },
    {
        dataKey: "SSL",
        dictionary: {},
        ignoredItems: []
    },
    {
        dataKey: "Redirects",
        dictionary: { "Redirects": "Redirected From" },
        ignoredItems: []
    },
    {
        dataKey: "Site Maps",
        dictionary: {},
        ignoredItems: []
    },
    {
        dataKey: "Open Ports",
        dictionary: {},
        ignoredItems: []
    },
    {
        dataKey: "Whois Info",
        dictionary: {},
        ignoredItems: []
    },
    {
        dataKey: "Screenshot",
        dictionary: {},
        ignoredItems: []
    },
    {
        dataKey: "Internal Links",
        dictionary: {},
        ignoredItems: []
    },
    {
        dataKey: "Linked Emails",
        dictionary: {},
        ignoredItems: []
    },
    {
        dataKey: "Linked Phone Numbers",
        dictionary: {},
        ignoredItems: []
    }
];

function getConfigByTitle(title) {
    return toolsConfig.find(tool => tool.dataKey === title || tool.containerSelector === title);
}

Object.defineProperty(String.prototype, 'capitalize', {
    value: function() {
        return this.charAt(0).toUpperCase() + this.slice(1);
    },
    enumerable: false
});

const eventSource = new EventSource('/events');
const columns = {
    col1: document.querySelector('.col1'),
    col2: document.querySelector('.col2'),
    col3: document.querySelector('.col3')
};

const columnMapping = {
    "Cookies": { column: 'col1', order: 2 },
    "IP Info": { column: 'col2', order: 1 },
    "Headers": { column: 'col3', order: 1 },
    "Domain": { column: 'col1', order: 3 },
    "SSL": { column: 'col2', order: 2 },
    "Redirects": { column: 'col3', order: 2 },
    "Site Maps": { column: 'col1', order: 4 },
    "Open Ports": { column: 'col2', order: 3 },
    "Whois Info": { column: 'col1', order: 1 },
    "Screenshot": { column: 'col1', order: 5 },
    "Internal Links": { column: 'col2', order: 4 },
    "Linked Emails": { column: 'col3', order: 3 },
    "Linked Phone Numbers": { column: 'col1', order: 6 }
};

let receivedEvents = 0;
const insertedCards = {
    col1: [],
    col2: [],
    col3: []
};

eventSource.onmessage = function(event) {
    const eventData = JSON.parse(event.data);
    const title = Object.keys(eventData)[0];
    const config = getConfigByTitle(title);

    const ignoredItems = config.ignoredItems;
    const dictionary = config.dictionary;

    const keys = Object.keys(eventData[title]);
    console.log(title);

    if (keys.length > 0) {
        let listItems = '';

        for (let key of keys) {
            if (!ignoredItems.includes(key)) {
                let label = key;

                if (dictionary[key]) {
                    label = dictionary[key];
                }
                listItems += `
                    <li class="list-group-item" data-label="${label.capitalize()}">${eventData[title][key]} </li>
                `;
            }
        }

        const cardHTML = `
        <div class="card" style="width: 20rem; max-height: 600px; overflow-y: auto;">
            <div class="card-body">
                <h5 class="card-title">
                    ${title}
                    <span class="question-mark" data-toggle="collapse" data-target="#cardDescription_${title}" aria-expanded="false" aria-controls="cardDescription_${title}">
                        <i>?</i>
                    </span>
                </h5>
                <div class="collapse" id="cardDescription_${title}">
                    <p class="card-text">${eventData[title]}</p>
                </div>
            </div>
            <ul class="list-group list-group-flush">
                ${listItems}
            </ul>
        </div>
        `;

        const { column, order } = columnMapping[title];
        const columnElement = columns[column];
        insertedCards[column].push({ order, cardHTML });

        insertedCards[column].sort((a, b) => a.order - b.order);
        columnElement.innerHTML = insertedCards[column].map(card => card.cardHTML).join('');
    }
    receivedEvents++;

    if (receivedEvents === 12) {
        eventSource.close();
    }
};

eventSource.onerror = function(event) {
    console.error("EventSource failed:", event);
    eventSource.close();
};
