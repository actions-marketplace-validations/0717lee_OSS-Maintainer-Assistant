export function Footer({ L }) {
  return (
    <footer className="container-main mt-2 border-t border-border py-6 pb-11 text-xs text-text-tertiary">
      {L.footer}
      <a
        href="https://github.com/0717lee/OSS-Maintainer-Assistant"
        target="_blank"
        rel="noopener"
        className="text-text-secondary hover:underline"
      >
        {L.source}
      </a>
    </footer>
  );
}
