export function PrivacyPage() {
  return (
    <article className="space-y-8">
      <header className="space-y-2">
        <h1 className="scroll-m-20 text-4xl font-extrabold tracking-tight">Privacy Policy</h1>
        <p className="text-muted-foreground">Last updated: January 2025</p>
      </header>

      <p className="leading-7">
        The Caving Incident Database collects limited data from users for the purposes of analytics
        and abuse prevention.
      </p>

      <section className="space-y-4">
        <h2 className="scroll-m-20 border-b pb-2 text-3xl font-semibold tracking-tight">
          Information We Collect
        </h2>

        <div className="space-y-4">
          <h3 className="scroll-m-20 text-2xl font-semibold tracking-tight">
            Automatically Collected Data
          </h3>
          <p className="leading-7">
            When you visit CIDB, we automatically collect certain information for monitoring,
            security, and service improvement purposes:
          </p>
          <ul className="my-6 ml-6 list-disc space-y-2">
            <li>
              <strong>IP addresses:</strong> We log IP addresses for security monitoring and to help
              diagnose technical issues. IP addresses are stored securely and are not used to
              identify individual users or track browsing behavior.
            </li>
            <li>
              <strong>Page view counts:</strong> We track aggregate view counts for incidents to
              understand which content is most useful to our users. This data is anonymous and
              cannot be linked to individual visitors.
            </li>
            <li>
              <strong>Search query analytics:</strong> We collect anonymized, aggregated data about
              search terms to improve search functionality. Individual searches are not associated
              with specific users.
            </li>
          </ul>
        </div>

        <div className="space-y-4">
          <h3 className="scroll-m-20 text-2xl font-semibold tracking-tight">Client-Side Storage</h3>
          <p className="leading-7">
            For your convenience, we store certain preferences and history locally in your browser:
          </p>
          <ul className="my-6 ml-6 list-disc space-y-2">
            <li>
              <strong>Search history:</strong> Your recent searches are stored locally in your
              browser and are never sent to our servers. You can disable this feature or clear your
              history at any time using the controls on the home page.
            </li>
            <li>
              <strong>Recently viewed incidents:</strong> A list of incidents you've recently viewed
              is stored in your browser for easy access. This data remains entirely on your device.
            </li>
            <li>
              <strong>Display preferences:</strong> Your theme preference (light/dark mode) and view
              settings are stored locally.
            </li>
          </ul>
          <p className="leading-7">
            <strong>Important:</strong> We cannot associate your identity with the content you view.
            Your browsing history within CIDB is stored only in your browser and is not transmitted
            to or stored on our servers.
          </p>
        </div>

        <div className="space-y-4">
          <h3 className="scroll-m-20 text-2xl font-semibold tracking-tight">
            Feedback and Reports
          </h3>
          <p className="leading-7">When you submit feedback or report an issue with an incident:</p>
          <ul className="my-6 ml-6 list-disc space-y-2">
            <li>
              We log the IP address associated with the submission for abuse prevention and to help
              us follow up on reports.
            </li>
            <li>
              If you provide an email address (which is optional), we store it solely to contact you
              regarding your feedback if clarification or follow-up is needed.
            </li>
            <li>
              The content of your feedback or report is stored to allow us to review and action it
              appropriately.
            </li>
          </ul>
          <p className="leading-7">
            Email addresses collected through feedback forms are used exclusively for responding to
            your submission and are not used for marketing or shared with third parties.
          </p>
        </div>
      </section>

      <section className="space-y-4">
        <h2 className="scroll-m-20 border-b pb-2 text-3xl font-semibold tracking-tight">
          Personal Data in Incident Reports
        </h2>
        <p className="leading-7">
          CIDB contains historical records of caving incidents compiled from published sources,
          safety reports, and other publicly available materials. These records may include names
          and other personal information of individuals involved in incidents.
        </p>
        <p className="leading-7">
          If you are identified in an incident report and wish to have your personal information
          removed or anonymized, you have the right to request this. We will review all such
          requests and, where appropriate, redact or remove identifying information while preserving
          the educational and safety value of the incident record.
        </p>
        <p className="leading-7">
          To request removal or modification of your personal data from an incident report, please
          use the "Report an issue" button on the relevant incident page and select "Privacy
          Concern" as the reason. Alternatively, use the general feedback button and include details
          of the incident and the information you would like addressed.
        </p>
      </section>

      <section className="space-y-4">
        <h2 className="scroll-m-20 border-b pb-2 text-3xl font-semibold tracking-tight">
          Third-Party Services
        </h2>

        <div className="space-y-4">
          <h3 className="scroll-m-20 text-2xl font-semibold tracking-tight">
            Sentry (Error Monitoring)
          </h3>
          <p className="leading-7">
            We use{" "}
            <a
              href="https://sentry.io"
              target="_blank"
              rel="noopener noreferrer"
              className="font-medium underline underline-offset-4 hover:text-primary"
            >
              Sentry
            </a>{" "}
            to monitor application errors and performance. When an error occurs, Sentry may collect:
          </p>
          <ul className="my-6 ml-6 list-disc space-y-2">
            <li>Technical information about the error</li>
            <li>Browser and device information</li>
            <li>Session replay data to help us understand and reproduce issues</li>
          </ul>
          <p className="leading-7">
            This data is used solely for debugging and improving application stability. For more
            information, see{" "}
            <a
              href="https://sentry.io/privacy/"
              target="_blank"
              rel="noopener noreferrer"
              className="font-medium underline underline-offset-4 hover:text-primary"
            >
              Sentry's Privacy Policy
            </a>
            .
          </p>
        </div>

        <div className="space-y-4">
          <h3 className="scroll-m-20 text-2xl font-semibold tracking-tight">Google Analytics</h3>
          <p className="leading-7">
            We use Google Analytics to understand how visitors interact with CIDB. This service
            collects anonymized usage data including pages visited, time spent on site, and general
            geographic location. Google Analytics uses cookies to collect this information. For more
            details, see{" "}
            <a
              href="https://policies.google.com/privacy"
              target="_blank"
              rel="noopener noreferrer"
              className="font-medium underline underline-offset-4 hover:text-primary"
            >
              Google's Privacy Policy
            </a>
            .
          </p>
        </div>
      </section>

      <section className="space-y-4">
        <h2 className="scroll-m-20 border-b pb-2 text-3xl font-semibold tracking-tight">Cookies</h2>
        <p className="leading-7">CIDB uses a minimal number of cookies:</p>
        <ul className="my-6 ml-6 list-disc space-y-2">
          <li>
            <strong>Visitor identifier:</strong> A randomly generated identifier stored in a cookie
            to help us count unique visitors. This identifier is not linked to any personal
            information.
          </li>
          <li>
            <strong>Third-party cookies:</strong> Google Analytics and Sentry may set their own
            cookies as described above.
          </li>
        </ul>
      </section>

      <section className="space-y-4">
        <h2 className="scroll-m-20 border-b pb-2 text-3xl font-semibold tracking-tight">
          Data Retention
        </h2>
        <ul className="my-6 ml-6 list-disc space-y-2">
          <li>
            Server logs containing IP addresses are retained for a limited period for security and
            operational purposes.
          </li>
          <li>
            Aggregated analytics data (search queries, view counts) is retained indefinitely as it
            contains no personally identifiable information.
          </li>
          <li>
            Feedback submissions and associated email addresses are retained until the feedback has
            been actioned, after which personal identifiers may be removed.
          </li>
        </ul>
      </section>

      <section className="space-y-4">
        <h2 className="scroll-m-20 border-b pb-2 text-3xl font-semibold tracking-tight">
          Your Rights
        </h2>
        <p className="leading-7">You have the right to:</p>
        <ul className="my-6 ml-6 list-disc space-y-2">
          <li>
            Clear your local browsing data (search history, viewed incidents) at any time using the
            controls provided or your browser settings.
          </li>
          <li>Disable search history tracking in the application.</li>
          <li>
            Request removal or anonymization of your personal information from incident reports.
          </li>
          <li>Request information about any personal data we may hold about you.</li>
          <li>Request deletion of any personal data associated with you.</li>
        </ul>
      </section>

      <section className="space-y-4">
        <h2 className="scroll-m-20 border-b pb-2 text-3xl font-semibold tracking-tight">Contact</h2>
        <p className="leading-7">
          If you have questions about this privacy policy or wish to exercise your data rights,
          please use the feedback button to contact us.
        </p>
      </section>

      <section className="space-y-4">
        <h2 className="scroll-m-20 border-b pb-2 text-3xl font-semibold tracking-tight">
          Changes to This Policy
        </h2>
        <p className="leading-7">
          We may update this privacy policy from time to time. Any changes will be reflected on this
          page with an updated revision date.
        </p>
      </section>
    </article>
  );
}
