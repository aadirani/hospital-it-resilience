# Runbooks (generic templates)

Short checklists to adapt for a specific site. Print them and keep a copy in the server room and at the nursing stations, because they'll be needed when the systems are down.

## 1. Grid power lost

1. Check that the UPS shows **on battery** and the monitoring alert arrived.
2. Check that the generator started and the transfer switch moved to generator power within the expected time.
3. If the generator **hasn't started within 2 minutes**, go to the generator and follow the facilities procedure, and tell the duty manager.
4. If the UPS battery falls **below 40%**, warn the departments that a shutdown may follow.
5. If it falls **below 20%**, shut down in this order: Tier 3 (email, file shares) → Tier 2 (billing) → Tier 1 last (HIS, LIS, PACS). Departments switch to paper downtime forms.
6. After power returns, start Tier 1 first, check that the databases are consistent, then start Tier 2 and Tier 3.
7. Log the event: start time, duration, battery minimum reached, anything that failed.

## 2. Internet lost

1. Confirm the firewall moved to the cellular failover link.
2. Tell staff that clinical systems are unaffected and that email or external services may be slow.
3. Check that guest Wi-Fi is blocked while on failover, to save cellular data.
4. Report the fault to the primary ISP and log the ticket number.
5. After recovery, check that the night's off-site backup completed or re-run it.

## 3. Virtualization host failed

1. Confirm the failure (host unreachable on the management VLAN, hardware alarms).
2. Start the Tier 1 VM replicas on the surviving host, in this order: database servers → application servers → PBX.
3. Check that users can log in to the HIS, and tell departments the possible data loss window (time of the last replica).
4. Start Tier 2 VMs if the surviving host has capacity.
5. Open a hardware case with the vendor and record how long it took to recover against the RTO.

## 4. Suspected ransomware

1. **Disconnect, don't power off**: unplug the network cable or disable the switch port of the affected machines. Powering off can destroy evidence that's only in memory.
2. If spreading is suspected, block traffic between VLANs at the firewall except clinical Tier 1 flows.
3. **Don't log in to the backup server from any machine on the main network.**
4. Tell management and follow the hospital's incident reporting obligations.
5. Find the scope: which machines and accounts, and since when.
6. Rebuild affected systems from known-clean images and restore data from the latest clean backup (immutable cloud or offline disk if the online copy is in doubt).
7. Reset all admin and service account passwords, and review MFA and firewall logs.
8. Write a post-incident review and update this runbook.

## 5. Monthly restore test

1. Pick one Tier 1 system and one random file share folder.
2. Restore both into an isolated test VLAN.
3. Check that the application starts and the data opens correctly.
4. Record the date, system, restore time and result. **No record = the test didn't happen.**
