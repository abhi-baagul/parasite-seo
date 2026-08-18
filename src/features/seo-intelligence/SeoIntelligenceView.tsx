"use client";

import { competitors, contentGaps, keywordIdeas, serpResults } from "@/data/mock";
import { PageScaffold } from "@/components/layout/PageScaffold";
import { StatusBadge } from "@/components/ui/StatusBadge";

export function SeoIntelligenceView() {
  return (
    <PageScaffold>
      <div className="row g-3">
        <div className="col-lg-6">
          <div className="surface-card h-100">
            <div className="p-3 border-bottom">
              <h2 className="section-title mb-0">Keyword research</h2>
              <p className="small text-muted mb-0">Placeholder dataset for the intelligence layer.</p>
            </div>
            <div className="table-responsive">
              <table className="table table-clean">
                <thead>
                  <tr>
                    <th>Term</th>
                    <th>Volume</th>
                    <th>Difficulty</th>
                    <th>Intent</th>
                    <th>Opportunity</th>
                  </tr>
                </thead>
                <tbody>
                  {keywordIdeas.map((row) => (
                    <tr key={row.term}>
                      <td>{row.term}</td>
                      <td>{row.volume}</td>
                      <td>{row.difficulty}</td>
                      <td>{row.intent}</td>
                      <td>{row.opportunity}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
        <div className="col-lg-6">
          <div className="surface-card h-100">
            <div className="p-3 border-bottom">
              <h2 className="section-title mb-0">SERP analysis</h2>
            </div>
            <div className="table-responsive">
              <table className="table table-clean">
                <thead>
                  <tr>
                    <th>Pos</th>
                    <th>Title</th>
                    <th>Type</th>
                  </tr>
                </thead>
                <tbody>
                  {serpResults.map((row) => (
                    <tr key={row.url}>
                      <td>{row.position}</td>
                      <td>
                        <div>{row.title}</div>
                        <div className="small text-muted">{row.url}</div>
                      </td>
                      <td>{row.type}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
        <div className="col-lg-6">
          <div className="surface-card h-100">
            <div className="p-3 border-bottom">
              <h2 className="section-title mb-0">Competitor analysis</h2>
            </div>
            <div className="table-responsive">
              <table className="table table-clean">
                <thead>
                  <tr>
                    <th>Domain</th>
                    <th>Overlap</th>
                    <th>Traffic</th>
                    <th>Gap</th>
                  </tr>
                </thead>
                <tbody>
                  {competitors.map((row) => (
                    <tr key={row.domain}>
                      <td>{row.domain}</td>
                      <td>{row.overlappingKeywords}</td>
                      <td>{row.estimatedTraffic}</td>
                      <td>{row.contentGap}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
        <div className="col-lg-6">
          <div className="surface-card h-100">
            <div className="p-3 border-bottom">
              <h2 className="section-title mb-0">Content gaps</h2>
            </div>
            <div className="table-responsive">
              <table className="table table-clean">
                <thead>
                  <tr>
                    <th>Topic</th>
                    <th>Competitors</th>
                    <th>Ours</th>
                    <th>Priority</th>
                  </tr>
                </thead>
                <tbody>
                  {contentGaps.map((row) => (
                    <tr key={row.topic}>
                      <td>{row.topic}</td>
                      <td>{row.competitorCoverage}</td>
                      <td>{row.ourCoverage}</td>
                      <td>
                        <StatusBadge value={row.priority} />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </PageScaffold>
  );
}
