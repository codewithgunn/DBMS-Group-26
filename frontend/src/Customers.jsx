import React, { useState, useEffect } from 'react';

export default function CustomersPage() {
    const [customers, setCustomers] = useState([]);
    const [searchTerm, setSearchTerm] = useState("");
    const [selectedTag, setSelectedTag] = useState("All");

    useEffect(() => {
        const fetchCustomers = async () => {
            try {
                const response = await fetch(`/api/customers?search=${searchTerm}&tag=${selectedTag}`);
                const data = await response.json();
                setCustomers(data);
            } catch (error) {
                console.error("Failed to fetch customers:", error);
            }
        };

        const delayDebounceFn = setTimeout(() => {
            fetchCustomers();
        }, 300);

        return () => clearTimeout(delayDebounceFn);
    }, [searchTerm, selectedTag]);

    return (
        <div className="customers-container fade-in">
            <div className="page-header-new">
                <div>
                    <h2 style={{fontSize: '1.875rem', color: 'var(--text-main)'}}>Loyalty Program</h2>
                    <p style={{color: 'var(--text-muted)'}}>Manage your restaurant's customer base and rewards.</p>
                </div>
            </div>

            <div className="controls-bar">
                <div className="search-wrapper">
                    <span className="search-icon">🔍</span>
                    <input
                        type="text"
                        placeholder="Search by name or phone..."
                        className="input-field search-input-new"
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                    />
                </div>
                
                <select 
                    className="input-field filter-select-new"
                    value={selectedTag}
                    onChange={(e) => setSelectedTag(e.target.value)}
                >
                    <option value="All">All Tiers</option>
                    <option value="VIP">🌟 VIP Tier</option>
                    <option value="Regular">🔁 Regular Tier</option>
                    <option value="New">👋 New Members</option>
                </select>
            </div>

            <div className="table-card-new">
                <table className="data-table">
                    <thead>
                        <tr>
                            <th>CUSTOMER NAME</th>
                            <th>PHONE NUMBER</th>
                            <th>VISITS</th>
                            <th>LOYALTY POINTS</th>
                            <th>MEMBERSHIP TIER</th>
                        </tr>
                    </thead>
                    <tbody>
                        {customers.length > 0 ? (
                            customers.map((c) => (
                                <tr key={c.customer_id}>
                                    <td className="font-bold">{c.name}</td>
                                    <td>{c.phone}</td>
                                    <td>{c.visit_count}</td>
                                    <td className="points-cell">{c.total_points} pts</td>
                                    <td>
                                        <span className={`tier-badge tier-${(c.cluster_tag || 'New').toLowerCase()}`}>
                                            {c.cluster_tag || 'New'}
                                        </span>
                                    </td>
                                </tr>
                            ))
                        ) : (
                            <tr>
                                <td colSpan="5" className="empty-state">
                                    No loyalty members found.
                                </td>
                            </tr>
                        )}
                    </tbody>
                </table>
            </div>

            <style dangerouslySetInnerHTML={{__html: `
                .customers-container {
                    padding: 2rem;
                    max-width: 1400px;
                    margin: 0 auto;
                }
                .page-header-new {
                    margin-bottom: 2rem;
                    display: flex;
                    justify-content: space-between;
                    align-items: flex-end;
                }
                .controls-bar {
                    display: flex;
                    gap: 1rem;
                    margin-bottom: 2rem;
                }
                .search-wrapper {
                    position: relative;
                    flex: 1;
                }
                .search-icon {
                    position: absolute;
                    left: 1rem;
                    top: 50%;
                    transform: translateY(-50%);
                    color: var(--text-muted);
                }
                .search-input-new {
                    padding-left: 2.75rem !important;
                    height: 3rem;
                    font-size: 1rem !important;
                }
                .filter-select-new {
                    width: 200px;
                    height: 3rem;
                    font-size: 1rem !important;
                }
                .table-card-new {
                    background: var(--card-bg);
                    border-radius: 1rem;
                    border: 1px solid var(--border);
                    overflow: hidden;
                    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
                }
                .data-table {
                    width: 100%;
                    border-collapse: collapse;
                }
                .data-table th {
                    text-align: left;
                    padding: 1rem 1.5rem;
                    background: var(--input-bg);
                    font-size: 0.75rem;
                    font-weight: 700;
                    color: var(--text-muted);
                    border-bottom: 1px solid var(--border);
                    letter-spacing: 0.05em;
                }
                .data-table td {
                    padding: 1.25rem 1.5rem;
                    border-bottom: 1px solid var(--border);
                    color: var(--text-main);
                }
                .font-bold {
                    font-weight: 700;
                    color: var(--text-main);
                }
                .points-cell {
                    font-weight: 800;
                    color: var(--primary);
                }
                .tier-badge {
                    padding: 0.375rem 0.75rem;
                    border-radius: 9999px;
                    font-size: 0.75rem;
                    font-weight: 700;
                    text-transform: uppercase;
                }
                .tier-vip { background: rgba(245, 158, 11, 0.1); color: #f59e0b; border: 1px solid rgba(245, 158, 11, 0.2); }
                .tier-regular { background: rgba(79, 70, 229, 0.1); color: var(--primary); border: 1px solid rgba(79, 70, 229, 0.2); }
                .tier-new { background: rgba(148, 163, 184, 0.1); color: var(--text-muted); border: 1px solid rgba(148, 163, 184, 0.2); }
                .empty-state {
                    text-align: center;
                    padding: 4rem !important;
                    color: var(--text-muted);
                }
            `}} />
        </div>
    );
}
