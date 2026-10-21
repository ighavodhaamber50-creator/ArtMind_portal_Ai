export default function Pager({ page, pages, onPage }) {
  if (pages <= 1) return null

  return (
    <nav className="pager" aria-label="Pages">
      <button className="btn btn-outline-dark btn-sm" disabled={page <= 1} onClick={() => onPage(page - 1)}>
        Previous
      </button>
      {Array.from({ length: pages }, (_, index) => index + 1).map((number) => (
        <button
          key={number}
          className={`pager-num${number === page ? ' is-current' : ''}`}
          aria-current={number === page ? 'page' : undefined}
          aria-label={`Page ${number}`}
          onClick={() => onPage(number)}
        >
          {number}
        </button>
      ))}
      <button className="btn btn-outline-dark btn-sm" disabled={page >= pages} onClick={() => onPage(page + 1)}>
        Next
      </button>
    </nav>
  )
}