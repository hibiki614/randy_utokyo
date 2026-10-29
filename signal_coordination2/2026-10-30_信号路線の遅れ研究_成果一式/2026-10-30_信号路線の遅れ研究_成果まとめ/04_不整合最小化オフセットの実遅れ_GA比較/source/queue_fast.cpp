#include <vector>
#include <algorithm>
#include <cmath>
struct Span { double s,e,r; };
constexpr double C=120.0,QFLOW=.5;
void append(std::vector<Span>& a,double s,double e,double r){
 if(e-s<=1e-12 || r<=0)return;
 if(!a.empty() && std::abs(a.back().r-r)<1e-12 && std::abs(s-a.back().e)<1e-9)a.back().e=e;
 else a.push_back({s,e,r});
}
std::vector<Span> queue(const std::vector<Span>& a,double x,double g,double end){
 std::vector<double> times={0.,end};
 for(auto p:a){if(p.s>=-1e-9 && p.s<=end+1e-9)times.push_back(p.s);if(p.e>=-1e-9 && p.e<=end+1e-9)times.push_back(p.e);}
 int ns=int(std::floor(-x/C))-2,ne=int(std::ceil((end-x)/C))+2;
 for(int k=ns;k<=ne;++k){double s=x+k*C,e=s+g;if(s>=-1e-9 && s<=end+1e-9)times.push_back(s);if(e>=-1e-9 && e<=end+1e-9)times.push_back(e);}
 std::sort(times.begin(),times.end());times.erase(std::unique(times.begin(),times.end()),times.end());
 std::vector<Span> out;size_t ai=0;double q=0.;
 for(size_t k=0;k+1<times.size();++k){double t=times[k],b=times[k+1],dt=b-t;if(dt<=1e-12)continue;
  while(ai<a.size() && a[ai].e<=t+1e-12)++ai;
  double lam=0.;if(ai<a.size() && a[ai].s<=t+1e-12 && t+1e-12<a[ai].e-1e-12)lam=a[ai].r;
  double phase=std::fmod(t+1e-9-x,C);if(phase<0)phase+=C;double mu=phase<g-1e-12?QFLOW:0.;
  if(q>1e-12){double change=lam-mu;
   if(change< -1e-12){double hit=t+q/(-change);if(hit<b-1e-12){append(out,t,hit,mu);append(out,hit,b,std::min(lam,mu));q=0.;continue;}}
   append(out,t,b,mu);q=std::max(0.,q+change*dt);
  }else{append(out,t,b,std::min(lam,mu));q=lam>mu+1e-12?(lam-mu)*dt:0.;}
 }
 return out;
}
double inv_integral(const std::vector<Span>& a,double n0,double n1){double N=0.,sum=0.;
 for(auto p:a){double last=N+p.r*(p.e-p.s),lo=std::max(N,n0),hi=std::min(last,n1);
  if(hi>lo+1e-12)sum+=(hi-lo)*p.s+((hi-N)*(hi-N)-(lo-N)*(lo-N))/(2*p.r);
  N=last;
 }
 if(N<n1-1e-7)return NAN;return sum;
}
double dir(int n,const double*L,double speed,const double*x,const double*g,int warm,bool rev){
 int source=rev?n-1:0;double total=0.;for(int j=0;j<n-1;++j)total+=L[j]/(speed/3.6);
 double end=(warm+3)*C+total+10*C;std::vector<Span>a;
 for(int k=0;k<warm+3;++k)append(a,x[source]+k*C,x[source]+k*C+g[source],QFLOW);
 double n0=QFLOW*g[source]*warm,n1=n0+QFLOW*g[source]*3;
 double entry=inv_integral(a,n0,n1);
 for(int j=0;j<n-1;++j){int link=rev?n-2-j:j,node=rev?n-2-j:j+1;double dt=L[link]/(speed/3.6);for(auto&p:a){p.s+=dt;p.e+=dt;}a=queue(a,x[node],g[node],end);}
 return (inv_integral(a,n0,n1)-entry)/(n1-n0)-total;
}
extern "C" double corridor_delay(int n,const double*L,double speed,const double*x,const double*g,int warm){
 double f=dir(n,L,speed,x,g,warm,false),b=dir(n,L,speed,x,g,warm,true);return (g[0]*f+g[n-1]*b)/(g[0]+g[n-1]);
}
