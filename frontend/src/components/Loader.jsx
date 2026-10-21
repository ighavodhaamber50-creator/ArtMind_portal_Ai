export default function Loader({ label = 'Loading...' }) {
  return (
    <div className="d-flex justify-content-center align-items-center gap-2 py-5 text-secondary">
      <div className="spinner-border spinner-border-sm" role="status" />
      <span>{label}</span>
    </div>
  )
}