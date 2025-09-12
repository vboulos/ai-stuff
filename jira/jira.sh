export JIRA_URL="https://issues.redhat.com"
export JIRA_USERNAME="rhn-support-vboulos"
export JIRA_API_TOKEN=$1
export JIRA_PROJECT="ACM"

MY_SECRET=$JIRA_USERNAME:$JIRA_API_TOKEN
ENCODED_SECRET=$(echo -n "$MY_SECRET" | base64)

python3 jira_ticket_manager.py comprehensive_analysis.json \
  --labels "PICS" "jira" \
  --components "PICS" \
  --fix-version "2.15.0" \
  --issue-type "Bug"